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
            raise ValueError(tmpl % qp)
    return param_list2str(p_list, prefix)


class Param(object):
    def __init__(self, default=None, prefix=None, **kw):
        self.prefix = prefix
        self.required = kw.pop('required', False)
        self.multi = kw.pop('multi', None)
        if kw:
            raise ValueError('unexpected keyword argument(s): %r' % kw)
        if default is not None:
            default = normalize_param(default, self.prefix, self.multi)
        self.default = default
        self._value = None

    @property
    def value(self):
        return self._value

    @property
    def value_list(self):
        return param_str2list(self._value)

    def set_value(self, new_val=None):
        self._orig_value = new_val
        norm_val = normalize_param(new_val, self.prefix, self.multi)
        self._value = norm_val or self.default
        if not self._value:
            raise ValueError('param is required')
        return self._value

    __call__ = set_value


class SingleParam(object):
    def __init__(self, *a, **kw):
        kw['multi'] = False
        return super(SingleParam, self).__init__(*a, **kw)


class MultiParam(object):
    def __init__(self, *a, **kw):
        kw['multi'] = False
        return super(SingleParam, self).__init__(*a, **kw)


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

    def extract_results(self, response):
        return response

    def store_results(self, results):
        self.results.extend(results)

    def fetch_and_store(self):
        resp = self.fetch()
        resp = self.post_process_response(resp)
        if not resp:
            print "that's an error: '%s'" % getattr(resp, 'url', '')
            return []
        try:
            new_results = self.extract_results(resp)
        except Exception:
            raise
        self.store_results(new_results)
        return new_results

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
    param_prefix = None        # e.g., 'gcm'
    query_param_name = None    # e.g., 'title'
    query_param_prefix = None  # e.g., 'Category:'

    def __init__(self, query_param, limit=None, *a, **kw):
        super(QueryOperation, self).__init__(query_param, limit, *a, **kw)
        self.cont_strs = []
        self.namespaces = kw.pop('namespaces', None)  # TODO: needs remapping/checking?
        self.kwargs = kw

    def set_query_param(self, qp):
        self._orig_query_param = qp
        if qp is None:
            qp = ''
        if is_scalar(qp):
            qp = unicode(qp)
        if isinstance(qp, basestring):
            qp = qp.split('|')
        if not self.is_multiargument() and len(qp) > 1:
            cn = self.__class__.__name__
            tmpl = '%s expected singular query parameter, not %r'
            raise ValueError(tmpl % (cn, qp))
        qp = join_multi_args(qp, self.query_param_prefix)
        super(QueryOperation, self).set_query_param(qp)

    def set_limit(self, limit):
        self._orig_limit = limit
        if limit is None and self.is_bijective():
            query_param = self.query_param
            if isinstance(query_param, basestring):
                query_param = query_param.split('|')
            if is_scalar(query_param):
                limit = 1
            else:
                limit = len(query_param)
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
        if hasattr(cls, 'multiargument'):
            return cls.multiargument
        static_params = cls.static_params
        query_param_name = cls.query_param_name
        if 'list' in static_params:
            return False
        if query_param_name.endswith('s'):
            # default behavior:
            # plural query parameter name assumed to mean multiargument.
            # if that's a problem, be explicit by setting class.multiargument
            return True
        return False

    @classmethod
    def is_bijective(cls):
        if hasattr(cls, 'bijective'):
            return cls.bijective
        if 'list' in cls.static_params:
            return False
        return True

    def get_cont_str(self, resp, params):
        #todo? fuzzy walker thing to walk down to self.param_prefix+'continue'?
        qc_val = resp.results.get(self.api_action + '-continue')
        if qc_val is None:
            return None
        for key in ('generator', 'prop', 'list'):
            if key in params:
                next_key = params[key]
                break
        else:
            raise KeyError("couldn't find contstr")
        return qc_val[next_key][self.param_prefix + 'continue']

    def prepare_params(self, **kw):
        params = dict(self.static_params)
        prefix = self.param_prefix

        params[self.query_param_name] = self.query_param
        params[prefix + 'limit'] = self.current_limit
        if self.last_cont_str:
            params[prefix + 'continue'] = self.last_cont_str
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
