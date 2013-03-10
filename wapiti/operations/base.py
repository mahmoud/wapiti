# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
from abc import ABCMeta

from collections import OrderedDict
from functools import wraps

import sys
from os.path import dirname, abspath
# just until ransom becomes its own package
sys.path.append(dirname(dirname(abspath(__file__))))
from ransom import Client

from params import SingleParam
from utils import PriorityQueue, MaxInt


# TODO: if input_field is None, maybe don't require subclasses to
# override __init__ somehow?
# TODO: use cont_str_key better for preparing parameters?
# TODO: per_call_limit mess
# TODO: abstracting away per-call limits by creating multiple
# operations of the same type
# TODO: separate structure for saving completed subops (for debugging?)

DEFAULT_API_URL = 'http://en.wikipedia.org/w/api.php'
IS_BOT = False

DEFAULT_HEADERS = {'User-Agent': ('Wapiti/0.0.0 Mahmoud Hashemi'
                                  ' mahmoudrhashemi@gmail.com') }

ALL = MaxInt('ALL')

DEFAULT_CLIENT = Client({'headers': DEFAULT_HEADERS})


class WapitiException(Exception):
    pass


class NoMoreResults(Exception):
    pass


class LimitSpec(object):
    def __init__(self, _max, bot_max=None):
        self.max = int(_max)
        self.bot_max = bot_max or (self.max * 10)

    def get_limit(self, is_bot=False):
        if is_bot:
            return self.bot_max
        return self.max

    def __int__(self):
        return self.max

    #def __repr__(self):
    #    ret = super(LimitSpec, self).__repr__()
    #    _, _, args = ret.partition('(')  # lulz
    #    return '%s(%s' % (self.__class__.__name__, args)


class ParamLimit(LimitSpec):
    pass


class QueryLimit(LimitSpec):
    # TODO: magnitudes?
    def __init__(self, _max, bot_max=None, mw_default=None):
        super(QueryLimit, self).__init__(_max, bot_max)
        self.mw_default = mw_default


PL_50_500 = ParamLimit(50, 500)
DEFAULT_QUERY_LIMIT = QL_50_500 = QueryLimit(50, 500, 10)


"""
Notes on "multiargument" and "bijective":

There are lots of ways to classify operations, and these are just a
couple.

"Multiargument" operations can take more than one search parameter
at once, such as the GetProtections operation. Others, can only take
one argument at a time, like GetCategory.

"Bijective" only return at most one result per argument. GetProtections
is an example of a bijective query. Bijective queries do not require an
explicit limit on the number of results to be set by the user.


Going forward, these attributes can be determined as follows:

 - Multiargument: determined by looking at an operation's
 `input_field`. If it is a SingleParam, then multiargument is false,
 if it's a MultiParam, then multiargument is true.

 - Bijective: determined by looking at an operation's `output_type`,
   which more accurately describes the *per-parameter* return type. If
   it is a list, then bijective is true, if it's a bare type, then
   bijective is false.
"""


def get_inputless_init(old_init):
    @wraps(old_init)
    def inputless_init(self, limit=None, **kw):
        return old_init(self, None, limit, **kw)
    return inputless_init


class OperationMeta(ABCMeta):
    def __new__(cls, name, bases, attrs):
        ret = super(OperationMeta, cls).__new__(cls, name, bases, attrs)
        if name == 'Operation' or name == 'QueryOperation':
            return ret  # TODO: add elegance?
        subop_chain = getattr(ret, 'subop_chain', [])
        try:
            input_field = ret.input_field
        except AttributeError:
            input_field = subop_chain[0].input_field
            ret.input_field = input_field
        if input_field is None:
            ret.__init__ = get_inputless_init(ret.__init__)
        else:
            input_field.required = True
        # TODO: run through subop_chain, checking the outputs match up
        try:
            output_type = ret.output_type
        except AttributeError:
            output_type = subop_chain[-1].output_type
            ret.output_type = output_type

        try:
            ret.singular_output_type = ret.output_type[0]
        except (TypeError, IndexError):
            ret.singular_output_type = ret.output_type

        # TODO: support manual overrides for the following?
        ret.is_multiargument = getattr(input_field, 'multi', False)
        ret.is_bijective = True
        if type(output_type) is list and output_type:
            ret.is_bijective = False

        return ret


class Recursive(object):
    def __init__(self, wrapped_type):
        self.wrapped_type = wrapped_type

    def __getitem__(self, key):
        if key == 0 or key == -1:
            return self.wrapped_type
        raise IndexError("go away")

    def __iter__(self):
        return iter((self.wrapped_type,))


class Operation(object):
    """
    An abstract class connoting some semblance
    of statefulness and introspection (e.g., progress monitoring).
    """
    __metaclass__ = OperationMeta

    subop_chain = []

    def __init__(self, input_param, limit=None, **kw):
        self.client = kw.pop('client', None)
        if self.client:
            self.api_url = self.client.api_url
            self.is_bot_op = self.client.is_bot
        else:
            self.api_url = kw.get('api_url', DEFAULT_API_URL)
            self.is_bot_op = False
        self.set_input_param(input_param)
        self.set_limit(limit)

        self.kwargs = kw
        self.started = False
        self.results = OrderedDict()

        subop_queues = OrderedDict()
        if self.subop_chain:
            for subop_type in self.subop_chain:
                subop_queues[subop_type] = PriorityQueue()
            first_subop_type = self.subop_chain[0]
            first_subop = first_subop_type(self.input_param,
                                           limit=ALL,
                                           client=self.client)
            subop_queues[first_subop_type].add(first_subop)
        self.subop_queues = subop_queues

    #@abstractmethod
    #def get_progress(self):
    #    pass

    #@abstractmethod
    #def get_relative_progress(self):
    #    pass

    def set_input_param(self, param):
        self._orig_input_param = self._input_param = param
        if self.input_field:
            self._input_param = self.input_field.get_value(param)

    @property
    def input_param(self):
        return self._input_param

    @property
    def source(self):
        return self.api_url

    def set_limit(self, limit):
        # TODO: use new limit structures
        # TODO: add support for callable limit getters?
        self._orig_limit = limit
        if isinstance(limit, Operation):
            self.parent = limit
        if self.is_bijective:
            value_list = self.input_field.get_value_list(self.input_param)
            limit = len(value_list)
        self._limit = limit

    @property
    def limit(self):
        if isinstance(self._limit, Operation):
            return self._limit.remaining
        return self._limit

    @property
    def remaining(self):
        # TODO: use new limit struct
        # TODO: what about suboperations?
        limit = self.limit
        return max(0, limit - len(self.results))

    def process(self):
        self.started = True
        task = self.get_current_task()
        print self, len(self.results), task
        if task is None:
            raise NoMoreResults()
        elif isinstance(task, Operation):
            results = task.process()
        elif callable(task):  # not actually used
            results = task()
        else:
            msg = 'task expected as Operation or callable, not: %r' % task
            raise TypeError(msg)
        # TODO: check resp for api errors/warnings
        # TODO: check for unrecognized parameter values
        new_results = self.store_results(task, results)
        return new_results

    def get_current_task(self):
        if not self.remaining:
            return None
        for subop_type, subop_queue in reversed(self.subop_queues.items()):
            while subop_queue:
                subop = subop_queue[-1]
                if subop.remaining:
                    return subop
                else:
                    subop_queue.pop()
        return None

    def store_results(self, task, results):
        new_res = []
        if isinstance(self.subop_chain, Recursive):
            new_res = self._update_results(results)
            op_type = self.subop_chain.wrapped_type
            new_subops = [op_type(r, limit=ALL) for r in new_res]
            for op in new_subops:
                self.subop_queues[op_type].add(op)
            return new_res

        task_type = type(task)
        if not self.subop_chain or task_type is self.subop_chain[-1]:
            new_res = self._update_results(results)
        else:
            i = self.subop_chain.index(task_type)
            new_subop_type = self.subop_chain[i + 1]
            for res in results:
                new_subop = new_subop_type(res, limit=ALL)
                self.subop_queues[new_subop_type].add(new_subop)
        return new_res

    def _update_results(self, results):
        ret = []
        for res in results:
            if not self.remaining:
                break
            unique_key = getattr(res, 'unique_key', res)
            if unique_key in self.results:
                continue
            self.results[unique_key] = res
            ret.append(res)
        return ret

    def process_all(self):
        while 1:  # TODO: +retry behavior
            try:
                self.process()
            except NoMoreResults:
                break
        return self.results.values()

    __call__ = process_all

    def __repr__(self):
        cn = self.__class__.__name__
        if self.input_field is None:
            return '%s(limit=%r)' % (cn, self.limit)
        tmpl = '%s(%r, limit=%r)'  # add dynamic-limity stuff
        try:
            ip_disp = self.input_param
        except:
            ip_disp = '(unprintable param)'
        return tmpl % (cn, ip_disp, self.limit)


class QueryOperation(Operation):
    api_action = 'query'
    #input_field = None
    field_prefix = None        # e.g., 'gcm'
    cont_str_key = None
    per_query_limit = QL_50_500
    default_limit = ALL

    def __init__(self, input_param, limit=None, **kw):
        if limit is None:
            limit = self.default_limit
        kw['limit'] = limit
        super(QueryOperation, self).__init__(input_param, **kw)
        self.cont_strs = []
        self._set_params()

    def _set_params(self):
        is_bot_op = self.is_bot_op

        params = {}
        for field in self.fields:
            pref_key = field.get_key(self.field_prefix)
            kw_val = self.kwargs.get(field.key)
            params[pref_key] = field.get_value(kw_val)
        if self.input_field:
            qp_key_pref = self.input_field.get_key(self.field_prefix)
            qp_val = self.input_field.get_value(self.input_param)
            params[qp_key_pref] = qp_val

            field_limit = self.input_field.limit or QL_50_500
            try:
                pq_pl = field_limit.get_limit(is_bot_op)
            except AttributeError:
                pq_pl = int(field_limit)
            self.per_query_param_limit = pq_pl
        self.params = params

        try:
            per_query_limit = self.per_query_limit.get_limit(is_bot_op)
        except AttributeError:
            per_query_limit = int(self.per_query_limit)
        self.per_query_limit = per_query_limit

        return

    @property
    def current_limit(self):
        return min(self.remaining, self.per_query_limit)

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
        if cls.input_field:
            query_key = cls.input_field.get_key(cls.field_prefix)
            ret[query_key] = cls.input_field
        return ret

    def get_current_task(self):
        if not self.remaining:
            return None
        params = self.prepare_params(**self.kwargs)
        # TODO: blargh
        client = lambda: None
        client.api_url = self.api_url
        mw_call = MediaWikiCall(params, client=client)
        return mw_call

    def prepare_params(self, **kw):
        params = dict(self.params)
        # TODO: should not include limit for bijective operations
        params[self.field_prefix + 'limit'] = self.current_limit
        if self.last_cont_str:
            params[self.cont_str_key] = self.last_cont_str
        params['action'] = self.api_action
        return params

    def post_process_response(self, response):
        """
        Used to rectify inconsistencies in API responses
        (looking at you, Feedback API)
        """
        return response.results.get(self.api_action)

    def extract_results(self, resp):
        raise NotImplementedError('inheriting classes should return'
                                  ' a list of results from the response')

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

    def store_results(self, task, resp):
        if resp.notices:  # TODO: lift this
            pass  # TODO: resolve some limit warnings
            #print "may have an error: %r (%r)" % (resp.notices, resp.url)
        processed_resp = self.post_process_response(resp)
        if processed_resp is None:
            return []  # TODO: keep an eye on this
        try:
            new_results = self.extract_results(processed_resp)
        except Exception:
            raise
        super(QueryOperation, self).store_results(task, new_results)
        new_cont_str = self.get_cont_str(resp)
        self.cont_strs.append(new_cont_str)
        return new_results


BASE_API_PARAMS = {'format': 'json',
                   'servedby': 'true'}


class MediaWikiCall(Operation):
    """
    Sets up actual API HTTP request, makes the request, encapsulates
    error handling, and stores results.
    """
    input_field = SingleParam('url_params')  # param_type=dict)
    output_type = Operation

    _limit = 1

    def __init__(self, params, **kw):
        # These settings will all go on the WapitiClient
        self.raise_exc = kw.pop('raise_exc', True)
        self.raise_err = kw.pop('raise_err', True)
        self.raise_warn = kw.pop('raise_warn', False)
        self.client = kw.pop('client')
        self.ransom_client = getattr(self.client, 'ransom_client', DEFAULT_CLIENT)
        if kw:
            raise ValueError('got unexpected keyword arguments: %r'
                             % kw.keys())
        self.api_url = self.client.api_url
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

        self._input_param = params

    def process(self):
        # TODO: add URL to all exceptions
        resp = None
        try:
            resp = self.ransom_client.get(self.api_url, self.params)
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

    @property
    def remaining(self):
        if self.done:
            return 0
        return 1

"""
GetCategoryPagesRecursive
(FlattenCategory -> GetCategoryPages -> Wikipedia API call -> URL fetch     )
(PageInfos       <- PageInfos        <- MediaWikiCall      <- RansomResponse)

operation's input_field = explicit or first field of chain

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
  - Provides a uniform way of checking progress (checking if it's done)

Some notes on Operation design/usage:
  - An Operation typically keeps a copy of its results internally,
  most likely a unique list of some sort, and should return only
  new results.
  - Calling an Operation directly calls process() repeatedly until the
  operation is complete, then returns the internally tracked results.

"""
