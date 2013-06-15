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
import ransom

from params import SingleParam
from models import get_unique_func, get_priority_func
from utils import (PriorityQueue,
                   MaxInt,
                   chunked_iter,
                   make_type_wrapper,
                   OperationExample)

# TODO: handle automatic redirecting better
# TODO: support batching and optimization limits
# TODO: concurrency. get_current_task() -> get_current_tasks()
# TODO: wrap exceptions
# TODO: separate structure for saving completed subops (for debugging?)
# TODO: WebRequestOperation: accepts URL, action (default: GET)
# TODO: Model links (url attribute)
# TODO: support field param_type (for cases with ints and strs)
# TODO: use source descriptor instead of api_url? (for op.source)
# TODO: check that subop_chain types match up
# TODO: check that priority attribute exists on output_type where applicable

"""
- what if operations were iterable over their results and process()
  returned the operation itself? (more expensive to iterate and find
  non-dupe results, would set ops help?)
- client -> root_owner.  parent operation (client
  if no parent op) -> owner.
- pregenerate MediawikiCalls/URLs on QueryOperations

Operation modifiers:
- Prioritized
- Recursive
- Buffered

fun metadata:

- operations executed
- suboperations skipped (from dedupe/prioritization/laziness)
- web requests executed, kb downloaded

retry strategies:

- absolute number of failures
- streaks/runs of failures
- fail if first operation fails
- reduce batch size/query limit on timeouts

prioritization/batching/concurrency implementation thoughts:

- hands-off implementation via multiplexing?
- separate priority queues for params and suboperations?
- fancy new datastructure with dedupe + priority queueing built-in
- buffering: do 3/5/10 GetCategoryInfos before fetching member pages
- early subop production based on next parameter priority
  sinking below a certain threshold?
  (e.g., next param's subcats=5 -> fetch more category infos)
"""

DEFAULT_API_URL = 'http://en.wikipedia.org/w/api.php'
DEFAULT_BASE_URL = 'http://en.wikipedia.org/wiki/'

DEFAULT_HEADERS = {'User-Agent': ('Wapiti/0.0.0 Mahmoud Hashemi'
                                  ' mahmoudrhashemi@gmail.com') }

ALL = MaxInt('ALL')
DEFAULT_MIN = 50


class WapitiException(Exception):
    pass


class NoMoreResults(Exception):
    pass


DEFAULT_WEB_CLIENT = ransom.Client({'headers': DEFAULT_HEADERS})


class MockClient(object):
    def __init__(self, is_bot=False, **kwargs):
        self.debug = kwargs.pop('debug', False)
        self.web_client = DEFAULT_WEB_CLIENT
        self.api_url = DEFAULT_API_URL
        self.is_bot = is_bot


DEFAULT_CLIENT = MockClient()


Tune = make_type_wrapper('Tune', [('priority', None), ('buffer', None)])
Recursive = make_type_wrapper('Recursive', [('is_recursive', True)])


def get_unwrapped_options(wr_type):
    try:
        return dict(wr_type._wrapped_dict), wr_type._wrapped
    except AttributeError:
        return {}, wr_type


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


class ParamLimit(LimitSpec):
    pass


class QueryLimit(LimitSpec):
    def __init__(self, _max, bot_max=None, mw_default=None, _min=None):
        super(QueryLimit, self).__init__(_max, bot_max)
        self.mw_default = mw_default
        if _min is None:
            _min = DEFAULT_MIN
        self.min = min(self.max, _min)


PL_50_500 = ParamLimit(50, 500)
QL_50_500 = QueryLimit(50, 500, 10)
DEFAULT_QUERY_LIMIT = QL_500_5000 = QueryLimit(500, 5000, 10)


def get_inputless_init(old_init):
    """
    Used for Operations like get_random() which don't take an input
    parameter.
    """
    if getattr(old_init, '_is_inputless', None):
        return old_init
    @wraps(old_init)
    def inputless_init(self, limit=None, **kw):
        kw['input_param'] = None
        return old_init(self, limit=limit, **kw)
    inputless_init._is_inputless = True
    return inputless_init


def operation_signature_doc(operation):
    if operation.input_field is None:
        doc_input = 'None'
    else:
        doc_input = operation.input_field.key
    doc_output = operation.singular_output_type.__name__
    doc_template = 'Input: %s, Output: %s'
    if not operation.is_bijective:
        doc_template = 'Input: %s, Output: List of %ss'
    return doc_template % (doc_input, doc_output)


class OperationMeta(ABCMeta):
    _all_ops = []

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
            output_type = subop_chain[-1].singular_output_type
            for st in subop_chain:
                if not st.is_bijective:
                    output_type = [output_type]
                    break
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

        for ex in getattr(ret, 'examples', []):
            ex.bind_op_type(ret)

        ret.__doc__ = (ret.__doc__ and ret.__doc__ + '\n\n') or ''
        ret.__doc__ += operation_signature_doc(ret)
        cls._all_ops.append(ret)
        return ret


class OperationQueue(object):
    # TODO: chunking/batching should probably happen here
    # with the assistance of another queue for prioritized params
    # (i.e., don't create subops so eagerly)
    def __init__(self, qid, op_type, default_limit=ALL):
        self.qid = qid
        options, unwrapped = get_unwrapped_options(op_type)
        self.op_type = op_type
        self.unwrapped_type = unwrapped
        self.options = options

        self.unique_key = options.get('unique_key', 'unique_key')
        self.unique_func = get_unique_func(self.unique_key)
        self.priority = options.get('priority', 0)
        self.priority_func = get_priority_func(self.priority)
        self.default_limit = default_limit

        self.param_set = set()
        self.op_queue = PriorityQueue()
        self._dup_params = []

    def enqueue(self, param, **kw):
        unique_key = self.unique_func(param)
        if unique_key in self.param_set:
            self._dup_params.append(unique_key)
            return
        priority = self.priority_func(param)
        kwargs = {'limit': self.default_limit}
        kwargs.update(kw)
        new_subop = self.op_type(param, **kwargs)
        new_subop._origin_queue = self.qid
        self.op_queue.add(new_subop, priority)
        self.param_set.add(unique_key)

    def enqueue_many(self, param_list, **kw):
        for param in param_list:
            self.enqueue(param, **kw)
        return

    def __len__(self):
        return len(self.op_queue)

    def peek(self, *a, **kw):
        return self.op_queue.peek(*a, **kw)

    def pop(self, *a, **kw):
        return self.op_queue.pop(*a, **kw)


class Operation(object):
    """
    An abstract class connoting some semblance of statefulness and
    introspection (e.g., progress monitoring).
    """
    __metaclass__ = OperationMeta

    subop_chain = []

    def __init__(self, input_param, limit=None, **kw):
        self.client = kw.pop('client', None)
        if self.client is None:
            self.client = DEFAULT_CLIENT
        self.api_url = self.client.api_url
        self.is_bot_op = self.client.is_bot

        self.set_input_param(input_param)
        self.set_limit(limit)

        self.kwargs = kw
        self.started = False
        self.results = OrderedDict()

        subop_queues = [OperationQueue(0, type(self))]
        if self.subop_chain:
            subop_queues.extend([OperationQueue(i + 1, st) for i, st
                                 in enumerate(self.subop_chain)])
            subop_queues[1].enqueue_many(self.input_param_list,
                                         client=self.client)
        self.subop_queues = subop_queues

    def get_progress(self):
        return len(self.results)

    def get_relative_progress(self):
        if self.limit and self.limit is not ALL:
            return len(self.results) / float(self.limit)
        return 0.0

    def set_input_param(self, param):
        self._orig_input_param = self._input_param = param
        if self.input_field:
            self._input_param = self.input_field.get_value(param)
            self._input_param_list = self.input_field.get_value_list(param)
        else:
            self._input_param = None
            self._input_param_list = []  # TODO: necessary?

    @property
    def input_param(self):
        return self._input_param

    @property
    def input_param_list(self):
        return self._input_param_list

    @property
    def source(self):
        return self.api_url

    def set_limit(self, limit):
        # TODO: add support for callable limit getters?
        self._orig_limit = limit
        if isinstance(limit, Operation):
            self.parent = limit
        if self.is_bijective and self.input_field:
            limit = len(self.input_param_list)
        self._limit = limit

    @property
    def limit(self):
        if isinstance(self._limit, Operation):
            return self._limit.remaining
        return self._limit

    @property
    def remaining(self):
        limit = self.limit
        if limit is None:
            limit = ALL
        return max(0, limit - len(self.results))

    def process(self):
        self.started = True
        task = self.get_current_task()
        if self.client.debug:
            print self.__class__.__name__, self.remaining
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
        for subop_queue in reversed(self.subop_queues):
            while subop_queue:
                subop = subop_queue.peek()
                if subop.remaining:
                    return subop
                else:
                    subop_queue.pop()
        return None

    def store_results(self, task, results):
        new_res = []
        oqi = getattr(task, '_origin_queue', None)
        if oqi is None:
            return self._update_results(results)
        dqi = oqi + 1

        origin_queue = self.subop_queues[oqi]
        is_recursive = origin_queue.options.get('is_recursive')
        if is_recursive:
            origin_queue.enqueue_many(results)
        if dqi < len(self.subop_queues):
            dest_queue = self.subop_queues[dqi]
            dest_queue.enqueue_many(results)
        else:
            new_res = self._update_results(results)
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
        tmpl = '%s(%s, limit=%r)'  # add dynamic-limity stuff
        try:
            ip_disp = repr(self.input_param)
        except:
            ip_disp = "'(unprintable param)'"
        return tmpl % (cn, ip_disp, self.limit)


class QueryOperation(Operation):
    api_action = 'query'
    field_prefix = None        # e.g., 'gcm'
    cont_str_key = None
    per_query_limit = DEFAULT_QUERY_LIMIT
    default_limit = ALL

    def __init__(self, input_param, limit=None, **kw):
        if limit is None:
            limit = self.default_limit
        super(QueryOperation, self).__init__(input_param, limit, **kw)
        self.cont_strs = []
        self._set_params()

        if self.is_bijective and self.input_param and \
                len(self.input_param_list) > self.per_query_param_limit:
            self.is_multiplexing = True
            self._setup_multiplexing()
        else:
            self.is_multiplexing = False

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

            field_limit = self.input_field.limit or PL_50_500
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

    def _setup_multiplexing(self):
        subop_queue = self.subop_queues[0]
        chunk_size = self.per_query_param_limit
        for chunk in chunked_iter(self.input_param_list, chunk_size):
            subop_queue.enqueue(tuple(chunk))  # TODO
        return

    @property
    def current_limit(self):
        ret = self.remaining
        if not self.is_bijective:
            ret = max(DEFAULT_MIN, ret)
        ret = min(ret, self.per_query_limit)
        return ret

    @property
    def remaining(self):
        if self.is_depleted:
            return 0
        return super(QueryOperation, self).remaining

    @property
    def last_cont_str(self):
        if not self.cont_strs:
            return None
        return self.cont_strs[-1]

    @property
    def is_depleted(self):
        if self.cont_strs and self.last_cont_str is None:
            return True
        return False

    @classmethod
    def get_field_dict(cls):
        ret = dict([(f.get_key(cls.field_prefix), f) for f in cls.fields])
        if cls.input_field:
            query_key = cls.input_field.get_key(cls.field_prefix)
            ret[query_key] = cls.input_field
        return ret

    def get_current_task(self):
        if self.is_multiplexing:
            return super(QueryOperation, self).get_current_task()
        if not self.remaining:
            return None
        params = self.prepare_params(**self.kwargs)
        mw_call = MediaWikiCall(params, client=self.client)
        return mw_call

    def prepare_params(self, **kw):
        params = dict(self.params)
        if not self.is_bijective:
            params[self.field_prefix + 'limit'] = self.current_limit
        if self.last_cont_str:
            params[self.cont_str_key] = self.last_cont_str
        params['action'] = self.api_action
        return params

    def post_process_response(self, response):
        """
        Used to rectify inconsistencies in API responses (looking at
        you, Feedback API)
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
        if self.is_multiplexing:
            return super(QueryOperation, self).store_results(task, resp)
        if resp.notices:  # TODO: lift this
            self._notices = list(resp.notices)
            self._url = resp.url
            print "may have an error: %r (%r)" % (resp.notices, resp.url)
        processed_resp = self.post_process_response(resp)
        if processed_resp is None:
            new_cont_str = self.get_cont_str(resp)  # TODO: DRY this.
            self.cont_strs.append(new_cont_str)
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
        self.web_client = getattr(self.client,
                                     'web_client',
                                     DEFAULT_WEB_CLIENT)
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
            resp = self.web_client.get(self.api_url, self.params)
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


class WebRequestOperation(Operation):
    input_field = SingleParam('url')
    output_type = Operation
    _limit = 1

    def __init__(self, input_param, **kw):
        self.client = kw.pop('client', None)
        self.web_client = getattr(self.client,
                                  'web_client',
                                  DEFAULT_WEB_CLIENT)
        self.action = kw.pop('action', 'get')
        self.raise_exc = kw.pop('raise_exc', True)
        if kw:
            raise ValueError('got unexpected keyword arguments: %r'
                             % kw.keys())
        self.set_input_param(input_param)
        self.url = self._input_param
        self.kwargs = kw
        self.results = {}

    def process(self):
        resp = None
        try:
            resp = self.web_client.req(self.action, self.url)
        except Exception as e:
            self.exception = e
            if self.raise_exc:
                raise
            return self
        self.results[self.url] = resp.text
        raise NoMoreResults()
        #return self


class GetPageHTML(Operation):
    input_field = SingleParam('title')
    examples = [OperationExample('Africa', limit=1)]
    output_type = Operation
    _limit = 1

    def __init__(self, *a, **kw):
        super(GetPageHTML, self).__init__(*a, **kw)
        self.web_client = getattr(self.client,
                                  'web_client',
                                  DEFAULT_WEB_CLIENT)
        self.raise_exc = kw.pop('raise_exc', True)
        source_info = getattr(self.client, 'source_info', None)
        if source_info:
            main_title = source_info.mainpage
            main_url = source_info.base
            self.base_url = main_url[:-len(main_title)]
        else:
            self.base_url = DEFAULT_BASE_URL
        self.url = self.base_url + self.input_param
        self.results = {}

    def process(self):
        try:
            resp = self.web_client.get(self.url)
        except Exception as e:
            self.exception = e
            if self.raise_exc:
                raise
            return self
        self.results[self.url] = resp.text
        raise NoMoreResults()
