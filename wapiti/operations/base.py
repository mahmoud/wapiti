# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import sys
from os.path import dirname
# just until ransom becomes its own package
sys.path.append(dirname(dirname((__file__))))

from functools import partial
import json

from ransom import Client, Response

DEFAULT_API_URL = 'http://en.wikipedia.org/w/api.php'
IS_BOT = False
if IS_BOT:
    PER_CALL_LIMIT = 5000
else:
    PER_CALL_LIMIT = 500

DEFAULT_LIMIT = 500  # TODO

DEFAULT_HEADERS = {'User-Agent': ('Wapiti/0.0.0 Mahmoud Hashemi'
                                  ' mahmoudrhashemi@gmail.com') }
MAX_LIMIT = sys.maxint

DEFAULT_CLIENT = Client({'headers': DEFAULT_HEADERS})

if IS_BOT:
    PER_CALL_LIMIT = 5000  # most of these globals will be set on client
else:
    PER_CALL_LIMIT = 500

# From http://en.wikipedia.org/wiki/Wikipedia:Namespace
NAMESPACES = {
    'Main': 0,
    'Talk': 1,
    'User': 2,
    'User talk': 3,
    'Wikipedia': 4,
    'Wikipedia talk': 5,
    'File': 6,
    'File talk': 7,
    'MediaWiki': 8,
    'MediaWiki talk': 9,
    'Template': 10,
    'Template talk': 11,
    'Help': 12,
    'Help talk': 13,
    'Category': 14,
    'Category talk': 15,
    'Portal': 100,
    'Portal talk': 101,
    'Book': 108,
    'Book talk': 109,
    'Special': -1,
    'Media': -2}


def is_scalar(obj):
    return not hasattr(obj, '__iter__') or isinstance(obj, basestring)


def prefixed(arg, prefix=None):
    if prefix and not arg.startswith(prefix):
        arg = prefix + arg
    return arg


def param_list2str(p_list, prefix=None, keep_empty=False):
    if is_scalar(p_list):
        p_list = param_str2list(p_list, keep_empty)
    u_p_list = [unicode(p) for p in p_list]
    ret = "|".join([prefixed(t, prefix)
                    for t in u_p_list if (t or keep_empty)])
    return unicode(ret)


def param_str2list(p, keep_empty=False):
    p = p or ''
    if is_scalar(p):
        p = unicode(p)
    else:
        p = param_list2str(p)
    p_list = p.split('|')
    if not keep_empty:
        p_list = [sp for sp in p_list if sp]
    return p_list


def normalize_param(p, prefix=None, multi=None):
    p_list = param_str2list(p)
    if multi is False:
        if len(p_list) > 1:
            tmpl = 'expected singular query parameter, not %r'
            raise ValueError(tmpl % p)
    return param_list2str(p_list, prefix)


class Param(object):
    def __init__(self, key, default=None, val_prefix=None, **kw):
        if not key:
            raise ValueError('expected name, not %r' % key)
        self.key = unicode(key)
        self.val_prefix = val_prefix
        self.key_prefix = kw.pop('key_prefix', True)  # True = filled in later
        self.required = kw.pop('required', False)
        self.multi = kw.pop('multi', None)
        if kw:
            raise ValueError('unexpected keyword argument(s): %r' % kw)
        if default is not None:
            default = normalize_param(default, self.val_prefix, self.multi)
        self.default = default

    def get_key(self, key_prefix=None):
        if self.key_prefix:
            prefix = key_prefix
            if prefix is None:
                prefix = self.key_prefix
            if isinstance(prefix, basestring):
                prefix = unicode(prefix)
            else:
                raise TypeError('expected valid string prefix')
        else:
            prefix = ''
        return prefix + self.key

    def get_value(self, value, prefix=None):
        if prefix is None:
            prefix = self.val_prefix
        norm_val = normalize_param(value, prefix, self.multi)
        val = norm_val or self.default
        if val is None and self.required:
            raise ValueError('%r param is required' % self.key)
        return val

    def get_value_list(self, value, prefix=None):
        return param_str2list(self.get_value(value, prefix))

    def get_tuple(self):
        return (self.key, self.value)

    def get_tuple_from_kwargs(self, **kwargs):
        """
        Picks up appropriate values from kwargs,
        returns the defaults if nothing matches.
        """
        pass

    __call__ = get_value


class StaticParam(Param):
    def __init__(self, key, value):
        super(StaticParam, self).__init__(key, value)

    def get_key(self, *a, **kw):
        return self.key

    def get_value(self, *a, **kw):
        return self.default


class SingleParam(Param):
    def __init__(self, *a, **kw):
        kw['multi'] = False
        super(SingleParam, self).__init__(*a, **kw)


class MultiParam(Param):
    def __init__(self, *a, **kw):
        kw['multi'] = True
        super(MultiParam, self).__init__(*a, **kw)


class NoMoreResults(Exception):
    pass


class Operation(object):
    """
    A mostly abstract class connoting some semblance
    of statefulness and introspection (e.g., progress monitoring).
    """

    def __init__(self):
        pass

    def parse_params(self, *a, **kw):
        pass

    def get_progress(self):
        pass

    def get_relative_progress(self):
        pass


"""
Notes on "multiargument" and "bijective":

There are lots of ways to classify query operations, and
these are just a couple.

"Multiargument" operations can take more than one search parameter
at once, such as the GetProtections operation. Others, can only take
one argument at a time, like GetCategory.

"Bijective" only return at most one result per argument. GetProtections
is an example of a bijective query. Bijective queries do not require an
explicit limit on the number of results to be set by the user.
"""
class BaseQueryOperation(Operation):
    source = None
    per_call_limit = PER_CALL_LIMIT
    default_limit = DEFAULT_LIMIT
    dynamic_limit = False

    def __init__(self, query_param, limit=None, *a, **kw):
        self.client = kw.pop('client', None)
        if self.client:
            self.api_url = self.client.api_url
        else:
            self.api_url = kw.pop('api_url', DEFAULT_API_URL)
        self.set_query_param(query_param)
        self.set_limit(limit)
        self.kwargs = kw

        self.started = False
        self.results = []

    @property
    def query_param(self):
        return self._query_param

    @property
    def limit(self):
        return self._get_limit()

    @property
    def source(self):
        return self.api_url

    def set_query_param(self, qp):
        self._query_param = qp

    def set_limit(self, limit):
        self.dynamic_limit = True
        if hasattr(limit, 'remaining'):
            self._get_limit = lambda: limit.remaining
        elif callable(limit):
            self._get_limit = limit
        else:
            self.dynamic_limit = False
            self._get_limit = lambda: limit

    @property
    def remaining(self):
        limit = self.limit or self.default_limit
        return max(0, limit - len(self.results))

    @property
    def current_limit(self):
        return min(self.remaining, self.per_call_limit)

    @classmethod
    def is_multiargument(cls):
        return getattr(cls, 'multiargument', False)

    @classmethod
    def is_bijective(cls):
        return getattr(cls, 'bijective', True)

    def fetch(self):
        raise NotImplementedError('inheriting classes should return'
                                  ' a list of results from the response')

    def post_process_response(self, response):
        """
        Used to rectify inconsistencies in API responses
        (looking at you, Feedback API)
        """
        return response

    def store_results(self, results):
        self.results.extend(results[:self.remaining])

    def get_current_task(self):
        if not self.remaining:
            return None
        return self.fetch_and_store

    def process(self):
        self.started = True
        task = self.get_current_task()
        if task is None:
            raise NoMoreResults()
        results = task()
        return results

    def process_all(self):
        while 1:  # TODO: +retry behavior
            try:
                self.process()
            except NoMoreResults:
                break
        return self.results

    __call__ = process_all

    def __repr__(self):
        cn = self.__class__.__name__
        if self.dynamic_limit:
            tmpl = '%s(%r, limit=lambda: %r)'
        else:
            tmpl = '%s(%r, limit=%r)'
        return tmpl % (cn, self.query_param, self.limit)


class QueryOperation(BaseQueryOperation):
    api_action = 'query'
    query_field = None
    field_prefix = None        # e.g., 'gcm'
    cont_str_key = None

    def __init__(self, query_param, limit=None, *a, **kw):
        super(QueryOperation, self).__init__(query_param, limit, *a, **kw)
        self.cont_strs = []
        self._set_params()

    def set_query_param(self, qp):
        self._orig_query_param = qp
        if self.query_field:
            qp = self.query_field.get_value(qp)
        super(QueryOperation, self).set_query_param(qp)

    def _set_params(self):
        params = {}
        for field in self.fields:
            pref_key = field.get_key(self.field_prefix)
            kw_val = self.kwargs.get(field.key)
            params[pref_key] = field.get_value(kw_val)
        if self.query_field:
            qp_key_pref = self.query_field.get_key(self.field_prefix)
            qp_val = self.query_field.get_value(self.query_param)
            params[qp_key_pref] = qp_val
        self.params = params

    def set_limit(self, limit):
        self._orig_limit = limit
        if limit is None and self.is_bijective():
            p_list = param_str2list(self.query_param)
            if is_scalar(p_list):
                limit = 1
            else:
                limit = len(p_list)
        super(QueryOperation, self).set_limit(limit)

    @property
    def remaining(self):
        if self.cont_strs and self.last_cont_str is None:
            return 0
        return super(QueryOperation, self).remaining

    @property
    def last_cont_str(self):
        if not self.cont_strs:
            return None
        return self.cont_strs[-1]

    @classmethod
    def is_multiargument(cls):
        return getattr(cls.query_field, 'multi', False)

    @classmethod
    def is_bijective(cls):
        if hasattr(cls, 'bijective'):
            return cls.bijective
        if 'list' in cls.get_field_dict():
            return False
        return True

    @classmethod
    def get_field_dict(cls):
        ret = dict([(f.get_key(cls.field_prefix), f) for f in cls.fields])
        if cls.query_field:
            ret[cls.query_field.get_key(cls.field_prefix)] = cls.query_field
        return ret

    def get_cont_str(self, resp):
        qc_val = resp.results.get(self.api_action + '-continue')
        if qc_val is None:
            return None
        for key in ('generator', 'prop', 'list'):
            if key in self.params:
                next_key = self.params[key]
                break
        else:
            raise KeyError("couldn't find contstr")
        if not self.cont_str_key:
            self.cont_str_key = qc_val[next_key].keys()[0]
        return qc_val[next_key][self.cont_str_key]

    def prepare_params(self, **kw):
        params = dict(self.params)
        # TODO: should not include limit for bijective operations
        params[self.field_prefix + 'limit'] = self.current_limit
        if self.last_cont_str:
            params[self.cont_str_key] = self.last_cont_str
        return params

    def fetch(self):
        params = self.prepare_params(**self.kwargs)
        mw_call = MediawikiCall(self.api_url, self.api_action, params).do_call()
        # TODO: check resp for api errors/warnings
        return mw_call

    def extract_results(self, resp):
        raise NotImplementedError('inheriting classes should return'
                                  ' a list of results from the response')

    def post_process_response(self, response):
        return response.results.get(self.api_action)

    def fetch_and_store(self):
        resp = self.fetch()
        if resp.notices:
            pass  # TODO: resolve some limit warnings
            #print "may have an error: %r (%r)" % (resp.notices, resp.url)
        processed_resp = self.post_process_response(resp)
        if processed_resp is None:
            return []
        try:
            new_results = self.extract_results(processed_resp)
        except Exception:
            raise
        self.store_results(new_results)
        new_cont_str = self.get_cont_str(resp)
        self.cont_strs.append(new_cont_str)
        return new_results


class SubjectResolvingQueryOperation(QueryOperation):
    def store_results(self, pages):
        if self.kwargs.get('resolve_to_subject'):
            pages = [p.get_subject_info() for p in pages]
        return super(SubjectResolvingQueryOperation, self).store_results(pages)


BASE_API_PARAMS = {'format': 'json',
                   'servedby': 'true'}


class WapitiException(Exception):
    pass


class MediawikiCall(object):
    """
    Sets up actual API HTTP request, makes the request, encapsulates
    error handling, and stores results.
    """
    def __init__(self, api_url, action, params=None, **kw):
        self.api_url = api_url
        self.action = action

        self.raise_exc = kw.pop('raise_exc', True)
        self.raise_err = kw.pop('raise_err', True)
        self.raise_warn = kw.pop('raise_warn', False)
        self.client = kw.pop('client', DEFAULT_CLIENT)
        if kw:
            raise ValueError('got unexpected keyword arguments: %r'
                             % kw.keys())
        params = params or {}
        self.params = dict(BASE_API_PARAMS)
        self.params.update(params)
        self.params['action'] = self.action

        self.url = ''
        self.results = None
        self.servedby = None
        self.exception = None
        self.error = None
        self.error_code = None
        self.warnings = []

    def do_call(self):
        # TODO: add URL to all exceptions
        resp = None
        try:
            resp = self.client.get(self.api_url, self.params)
        except Exception as e:
            # TODO: log
            self.exception = e  # TODO: wrap
            if self.raise_exc:
                raise
            return self
        finally:
            self.url = getattr(resp, 'url', '')

        try:
            self.results = json.loads(resp.text)
        except Exception as e:
            self.exception = e  # TODO: wrap
            if self.raise_exc:
                raise
            return self
        self.servedby = self.results.get('servedby')

        error = self.results.get('error')
        if error:
            self.error = error.get('info')
            self.error_code = error.get('code')

        warnings = self.results.get('warnings', {})
        for mod_name, warn_dict in warnings.items():
            warn_str = '%s: %s' % (mod_name, warn_dict.get('*', warn_dict))
            self.warnings.append(warn_str)

        if self.error and self.raise_err:
            raise WapitiException(self.error_code)
        if self.warnings and self.raise_warn:
            raise WapitiException('warnings: %r' % self.warnings)
        return self

    @property
    def notices(self):
        ret = []
        if self.exception:
            ret.append(self.exception)
        if self.error:
            ret.append(self.error)
        if self.warnings:
            ret.extend(self.warnings)
        return ret


from heapq import heappush, heappop
import itertools
REMOVED = '<removed-task>'
class PriorityQueue(object):
    """
    Real quick type based on the heapq docs.
    """
    def __init__(self):
        self._pq = []
        self._entry_map = {}
        self.counter = itertools.count()

    def add(self, task, priority=None):
        # larger numbers = higher priority
        # todo: more complex logics
        priority = -int(priority or 0)
        if task in self._entry_map:
            self.remove_task(task)
        count = next(self.counter)
        entry = [priority, count, task]
        self._entry_map[task] = entry
        heappush(self._pq, entry)

    def remove(self, task):
        entry = self._entry_map.pop(task)
        entry[-1] = REMOVED

    def pop(self):
        while self._pq:
            priority, count, task = heappop(self._pq)
            if task is not REMOVED:
                del self._entry_map[task]
                return task
        raise KeyError('pop from an empty priority queue')

    def __len__(self):
        return len(self._entry_map)

    def __getitem__(self, index):
        # this is hacky! could make a sorted copy from the
        # heap and index into that at some point.
        if index != -1:
            raise IndexError('priority queues only support indexing on -1')
        _, _, task = self._pq[0]
        return task


class CompoundQueryOperation(BaseQueryOperation):
    def __init__(self, *a, **kw):
        generator = kw.pop('generator', None)
        super(CompoundQueryOperation, self).__init__(*a, **kw)

        self.suboperations = PriorityQueue()
        root_op_kwargs = dict(self.kwargs)
        root_op_kwargs['query_param'] = self.query_param
        root_op_kwargs['limit'] = self
        root_op = self.suboperation_type(**root_op_kwargs)
        self.suboperations.add(root_op)

        self.setup_generator(generator)

    def setup_generator(self, generator=None):
        if isinstance(generator, Operation):
            self.generator = generator
            return
        generator_type = getattr(self, 'default_generator', None)
        if not generator_type:
            self.generator = None
            return
        gen_kw_tmpl = getattr(self, 'generator_params', {})
        gen_kw = {'query_param': self.query_param }
        if not generator_type.is_bijective():
            gen_kw['limit'] = MAX_LIMIT
        for k, v in gen_kw_tmpl.items():
            if callable(v):
                gen_kw[k] = v(self)
        self.generator = generator_type(**gen_kw)
        return

    def produce_suboperations(self):
        if not self.generator or not self.generator.remaining:
            return None
        ret = []
        generated = self.generator.process()
        subop_kw_tmpl = getattr(self, 'suboperation_params', {})
        for g in generated:
            subop_kw = dict(self.kwargs)
            for k, v in subop_kw_tmpl.items():
                if callable(v):
                    subop_kw[k] = v(g)
            priority = subop_kw.pop('priority', 0)
            subop_kw['limit'] = self
            subop = self.suboperation_type(**subop_kw)
            self.suboperations.add(subop, priority)
            ret.append(subop)
        return ret

    def get_current_task(self):
        if not self.remaining:
            return None
        while 1:
            while self.suboperations:
                subop = self.suboperations[-1]
                if subop.remaining:
                    print subop, len(self.suboperations), len(self.results)
                    return partial(self.fetch_and_store, op=subop)
                else:
                    self.suboperations.pop()
            if not self.generator or not self.generator.remaining:
                break
            else:
                self.produce_suboperations()
        return None

    def fetch_and_store(self, op):
        try:
            res = op.process()
        except NoMoreResults:
            return []
        return self.store_results(res)
