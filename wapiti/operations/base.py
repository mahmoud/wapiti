# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import sys
from os.path import dirname
# just until ransom becomes its own package
sys.path.append(dirname(dirname((__file__))))

from functools import partial
import json

from ransom import Client, Response

from models import WikiException

DEFAULT_TIMEOUT  = 15
import socket
socket.setdefaulttimeout(DEFAULT_TIMEOUT)  # TODO: better timeouts for reqs


IS_BOT = False
if IS_BOT:
    PER_CALL_LIMIT = 5000
else:
    PER_CALL_LIMIT = 500

DEFAULT_LIMIT = 500  # TODO

SOURCES = {'enwp': 'http://en.wikipedia.org/w/api.php'}
API_URL = SOURCES['enwp']  # TODO: hardcoded for nowskies
IS_BOT = False
DEFAULT_RETRIES = 0
DEFAULT_HEADERS = {'User-Agent': ('Wapiti/0.0.0 Mahmoud Hashemi'
                                  'mahmoudrhashemi@gmail.com') }
MAX_LIMIT = sys.maxint
MAX_ARTICLES_LIST = 50

requests = Client({'headers': DEFAULT_HEADERS})

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
    ret = "|".join([prefixed(t, prefix) for t in p_list if (t or keep_empty)])
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
        if val is None:
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
    Mostly an abstract class representing an operation that can
    be performed by the Mediawiki API. Connotes some semblance
    of statefulness and introspection (e.g., progress monitoring).
    """
    api_action = None
    source = 'enwp'  # TODO: hardcode for the moment

    def __init__(self):
        pass

    def parse_params(self, *a, **kw):  # arguments?
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
    per_call_limit = PER_CALL_LIMIT
    default_limit = DEFAULT_LIMIT
    dynamic_limit = False

    def __init__(self, query_param, limit=None, *a, **kw):
        self.set_query_param(query_param)
        self.set_limit(limit)

        self.started = False
        self.results = []

    @property
    def query_param(self):
        return self._query_param

    @property
    def limit(self):
        return self._get_limit()

    def set_query_param(self, qp):
        self._query_param = qp

    def set_limit(self, limit):
        self.dynamic_limit = True
        if hasattr(limit, 'remaining'):  # replaces 'owner' functionality
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
        self.results.extend(results)

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

    def __init__(self, query_param, limit=None, *a, **kw):
        super(QueryOperation, self).__init__(query_param, limit, *a, **kw)
        self.cont_strs = []
        self.kwargs = kw
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

    def get_cont_str(self, resp, params):
        #todo? fuzzy walker thing to walk down to self.field_prefix+'continue'?
        qc_val = resp.results.get(self.api_action + '-continue')
        if qc_val is None:
            return None
        for key in ('generator', 'prop', 'list'):
            if key in params:
                next_key = params[key]
                break
        else:
            raise KeyError("couldn't find contstr")
        return qc_val[next_key][self.field_prefix + 'continue']

    def prepare_params(self, **kw):
        params = dict(self.params)
        params[self.field_prefix + 'limit'] = self.current_limit
        if self.last_cont_str:
            params[self.field_prefix + 'continue'] = self.last_cont_str
        return params

    def fetch(self):
        params = self.prepare_params(**self.kwargs)
        resp = api_req(self.api_action, params)
        # TODO: check resp for api errors/warnings

        new_cont_str = self.get_cont_str(resp, params)
        self.cont_strs.append(new_cont_str)
        return resp

    def extract_results(self, resp):
        raise NotImplementedError('inheriting classes should return'
                                  ' a list of results from the response')

    def post_process_response(self, response):
        return response.results.get(self.api_action)

    def fetch_and_store(self):
        resp = self.fetch()
        resp = self.post_process_response(resp)
        if not resp:
            print "that's an error: '%s'" % getattr(resp, 'url', '')
            import pdb;pdb.set_trace()
            return []
        try:
            new_results = self.extract_results(resp)
        except Exception:
            raise
        self.store_results(new_results)
        return new_results


class SubjectResolvingQueryOperation(QueryOperation):
    def store_results(self, pages):
        if self.kwargs.get('resolve_to_subject'):
            pages = [p.get_subject_identifier() for p in pages]
        return super(SubjectResolvingQueryOperation, self).store_results(pages)


def api_req(action, params=None, raise_exc=True, **kwargs):
    all_params = {'format': 'json',
                  'servedby': 'true'}
    all_params.update(kwargs)
    all_params.update(params)
    all_params['action'] = action
    headers = {'accept-encoding': 'gzip'}

    resp = Response()
    resp.results = None
    try:
        if action == 'edit':
            #TODO
            resp = requests.post(API_URL, params=all_params, headers=headers, timeout=DEFAULT_TIMEOUT)
        else:
            resp = requests.get(API_URL, all_params)
    except Exception as e:
        if raise_exc:
            raise
        else:
            resp.error = e
            resp.results = None
            return resp

    try:
        resp.results = json.loads(resp.text)
        resp.servedby = resp.results.get('servedby')
        # TODO: warnings?
    except Exception as e:
        if raise_exc:
            raise
        else:
            resp.error = e
            resp.results = None
            resp.servedby = None
            return resp

    mw_error = resp.headers.getheader('MediaWiki-API-Error')
    if mw_error:
        error_str = mw_error
        error_obj = resp.results.get('error')
        if error_obj and error_obj.get('info'):
            error_str += ' ' + error_obj.get('info')
        if raise_exc:
            raise WikiException(error_str)
        else:
            resp.error = error_str
            return resp

    return resp

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
        root_op_kwargs = dict(kw)
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
        gen_kw = {'query_param': self.query_param,
                  'limit': MAX_LIMIT}
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
            subop_kw = {}
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
