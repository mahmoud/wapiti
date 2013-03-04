# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from functools import partial
import json

import sys
from os.path import dirname
# just until ransom becomes its own package
sys.path.append(dirname(dirname((__file__))))
from ransom import Client

from params import param_str2list, SingleParam, StaticParam, MultiParam  # tmp
from utils import PriorityQueue, is_scalar


# TODO: if query_field is None, maybe don't require subclasses to
# override __init__ somehow?
# TODO: use an OrderedSet for results for automatic deduplication
# TODO: use cont_str_key better for preparing parameters?
# TODO: QueryParam that str()s to bar-separated string,
# but is actually an list/tuple/iterable
# TODO: parameter "coercion"
# TODO: per_call_limit mess
# TODO: abstracting away per-call limits by creating multiple
# operations of the same type

DEFAULT_API_URL = 'http://en.wikipedia.org/w/api.php'
IS_BOT = False
if IS_BOT:
    PER_CALL_LIMIT = 5000  # most of these globals will be set on client
else:
    PER_CALL_LIMIT = 500

DEFAULT_LIMIT = 500  # TODO

DEFAULT_HEADERS = {'User-Agent': ('Wapiti/0.0.0 Mahmoud Hashemi'
                                  ' mahmoudrhashemi@gmail.com') }
MAX_LIMIT = sys.maxint

DEFAULT_CLIENT = Client({'headers': DEFAULT_HEADERS})


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


class WapitiException(Exception):
    pass


class NoMoreResults(Exception):
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


Going forward, these attributes can be determined as follows:

 - Multiargument: determined by looking at an operation's
 `query_field`. If it is a SingleParam, then multiargument is false,
 if it's a MultiParam, then multiargument is true.

 - Bijective: determined by looking at an operation's `return_type`,
   which more accurately describes the *per-parameter* return type. If
   it is a list, then bijective is true, if it's a bare type, then
   bijective is false.
"""


class BaseQueryOperation(OperationBase):
    source = None
    per_call_limit = PER_CALL_LIMIT
    default_limit = DEFAULT_LIMIT
    dynamic_limit = False

    def __init__(self, query_param, limit=None, *a, **kw):
        self.client = kw.get('client', None)
        if self.client:
            self.api_url = self.client.api_url
        else:
            self.api_url = kw.get('api_url', DEFAULT_API_URL)
        self.set_query_param(query_param)
        self.set_limit(limit)
        self.kwargs = kw

        self.started = False
        self.results = []

    @property
    def limit(self):
        return self._get_limit()

    @property
    def source(self):
        return self.api_url

    def set_limit(self, limit):
        self._orig_limit = limit
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
        params['action'] = self.api_action
        return params

    def fetch(self):
        params = self.prepare_params(**self.kwargs)
        mw_call = MediawikiCall(self.api_url, params)
        mw_call.process()
        # TODO: check resp for api errors/warnings
        # TODO: check for unrecognized paramater values
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


class MediawikiCall(object):
    """
    Sets up actual API HTTP request, makes the request, encapsulates
    error handling, and stores results.
    """
    def __init__(self, api_url, params, **kw):
        self.api_url = api_url

        # These settings will all go on the WapitiClient
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
        self.action = params['action']

        self.url = ''
        self.results = None
        self.servedby = None
        self.exception = None
        self.error = None
        self.error_code = None
        self.warnings = []

    def process(self):
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
        gen_kw = {'query_param': self.query_param}
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
                return self.produce_suboperations
        return None

    def fetch_and_store(self, op):
        try:
            res = op.process()
        except NoMoreResults:
            return []
        return self.store_results(res)

"""
GetCategoryPagesRecursive
(FlattenCategory -> GetCategoryPages -> Wikipedia API call -> URL fetch     )
(PageInfos       <- PageInfos        <- MediaWikiCall      <- RansomResponse)

operation's query_field = explicit or first field of chain

def process(op):
   res = op.process()
   return self.store_results(res)

what about producing subops?

def process():
   task = self.get_current_task()
   res = task.process()
   if res and isinstance(res[0], Operation):
      self.store_subops(res)
      return  # return subops?
   return self.store_results(res)  # returns *new* results

GetCategoryPagesRecursive
(FlattenCategory --(CatInfos)->
        GetCategoryPages --("APIParamStructs")->
               MediawikiCall [--(url)-> URL fetch])

An "APIParamStruct" is really just something with the API url and param
dictionary, so QueryOperations themselves could be viewed as
APIParamStructs. In other words, hopefully no new model type needed
just for that.

At its most basic level, an Operation is something which:

  - Has a type-declared input field, and a declared return type
  - Has a process() function that returns results (of the output type)
    or raises NoMoreResults
  - Most likely takes a WapitiClient as a 'client' keyword
    argument in its __init__()
  - Provides a uniform way of checking progress

Some notes on Operation design/usage:
  - An Operation typically keeps a copy of its results internally,
  most likely a unique list of some sort, and should return only
  new results.
  - Calling an Operation directly calls process() repeatedly until the
  operation is complete, then returns the internally tracked results.

"""

from abc import ABCMeta, abstractmethod

class OperationMeta(ABCMeta):
    def __new__(cls, name, bases, attrs):
        ret = super(OperationMeta, cls).__new__(cls, name, bases, attrs)
        if name == 'OperationBase':
            return ret  # TODO: add elegance?
        subop_chain = getattr(ret, 'subop_chain', [])
        try:
            query_field = ret.query_field
        except AttributeError:
            query_field = subop_chain[0].query_field
            ret.query_field = query_field
        if query_field is None:
            # TODO: better support for random(), etc. (has no query field)
            pass
        # TODO: run through subop_chain, checking the outputs match up
        try:
            return_type = ret.return_type
        except AttributeError:
            return_type = subop_chain[-1].return_type
            ret.return_type = return_type

        try:
            ret.singular_return_type = ret.return_type[0]
        except (TypeError, IndexError):
            ret.singular_return_type = ret.return_type

        # TODO: support manual overrides for the following?
        ret.is_multiargument = getattr(query_field, 'multi', False)
        ret.is_bijective = True
        if type(return_type) is list and return_type:
            ret.is_bijective = False

        return ret

_MISSING = object()

class OperationBase(object):
    """
    An abstract class connoting some semblance
    of statefulness and introspection (e.g., progress monitoring).
    """
    __metaclass__ = OperationMeta
    # input_field = _MISSING  # TODO: etc.
    # output_type
    # subop_chain

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def get_progress(self):
        pass

    @abstractmethod
    def get_relative_progress(self):
        pass

    @abstractmethod
    def process(self):
        pass

    @property
    def input_param(self):
        return self._input_param

    def set_input_param(self, param):
        self._orig_input_param = param
        self._input_param = self.input_field.get_value(param)


class QueryOperation(OperationBase):
    api_action = 'query'

    def __init__(self, query_param, **kw):
        self.client = kw.pop('client', None)
        if self.client:
            self.api_url = self.client.api_url
        else:
            self.api_url = kw.get('api_url', DEFAULT_API_URL)
        limit = kw.pop('limit', None)
        self.set_limit(limit)

        self.kwargs = kw
        self.started = False
        self.results = []  # TODO: orderedset-like thing

        super(QueryOperation, self).__init__(**kw)

    def set_limit(self, limit):
        # TODO: use new limit structures
        # TODO: add support for callable limit getters?
        if isinstance(limit, QueryOperation):
            self.parent = limit
        self._limit = limit

    @property
    def limit(self):
        if isinstance(self._limit, QueryOperation):
            return self._limit.remaining
        return self._limit

    @property
    def remaining(self):
        # TODO: use new limit struct
        # TODO: what about suboperations?
        limit = self.limit or self.default_limit
        return max(0, limit - len(self.results))

    @property
    def current_limit(self):
        # TODO: use new limit struct
        return min(self.remaining, self.per_call_limit)

    def process(self):
        self.started = True
        task = self.get_current_task()
        if task is None:
            raise NoMoreResults()
        results = task.process()
        self.get_subops(task, results)
        return results

    def store_results(self, task, results):
        if type(subop_chain) is Recursive:
            pass
        if self.subop_chain[-1] is type(task):
            self.real_results.extend(results)
        else:
            i = self.subop_chain.index(type(task))
            new_subops = [self.subop_chain[i+1](res) for res in results]
            self.subop_queues[i].extend(new_subops)
        return

    def get_current_task(self):
        if not self.remaining:
            return None
        while 1:
            while self.suboperations:
                subop = self.suboperations[-1]
                if subop.remaining:
                    pass  # return subop
                else:
                    self.suboperations.pop()
            pass
        return
