# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import sys
from os.path import dirname
# just until ransom becomes its own package
sys.path.append(dirname(dirname((__file__))))

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
DEFAULT_MAX_COUNT = sys.maxint
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


def join_multi_args(orig_args, prefix=None):
    if isinstance(orig_args, basestring):
        args = orig_args.split('|')
    else:
        args = list(orig_args)
    return u"|".join([prefixed(t, prefix) for t in args])


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


class QueryOperation(Operation):
    api_action = 'query'
    param_prefix = None        # e.g., 'gcm'
    query_param_name = None    # e.g., 'title'
    query_param_prefix = None  # e.g., 'Category:'

    def __init__(self, query_param, limit=None, namespaces=None, retries=DEFAULT_RETRIES, **kw):
        self._orig_query_param = query_param
        self._set_query_param(query_param)
        self._set_limit(limit)

        self.started = False
        self.cont_strs = []
        self.max_retries = retries
        self.retries = 0
        self.results = []

        self.namespaces = namespaces  # TODO: needs remapping/checking?
        self.kwargs = kw

    def _set_query_param(self, query_param):
        if query_param is None:
            query_param = ''
        if is_scalar(query_param):
            query_param = unicode(query_param)
        if isinstance(query_param, basestring):
            query_param = query_param.split('|')
        if not self.is_multiargument() and len(query_param) > 1:
            raise ValueError('operation expected single argument, not %r'
                             % query_param)
        query_param = join_multi_args(query_param, self.query_param_prefix)
        self.query_param = query_param

    def _set_limit(self, limit):
        if limit is None and self.is_bijective():
            query_param = self.query_param
            if isinstance(query_param, basestring):
                query_param = query_param.split('|')
            if is_scalar(query_param):
                limit = 1
            else:
                limit = len(query_param)
        self.limit = limit

    def get_query_param(self):
        return self.query_param

    def get_query_param_name(self):
        return self.query_param_name

    @property
    def last_cont_str(self):
        if not self.cont_strs:
            return None
        return self.cont_strs[-1]

    @property
    def remaining(self):
        if not self.limit:
            return DEFAULT_LIMIT  # TODO
        return self.limit - len(self.results)

    def prepare_params(self, limit, cont_str, **kw):
        params = dict(self.static_params)
        query_param_name = self.get_query_param_name()
        query_param = self.get_query_param()
        prefix = self.param_prefix

        params[query_param_name] = query_param
        params[prefix + 'limit'] = min(limit, PER_CALL_LIMIT)
        if cont_str:
            params[prefix + 'continue'] = cont_str
        return params

    def fetch(self, params):
        return api_req(self.api_action, params)

    def extract_results(self, resp):
        """
        inheriting classes should return a list from the query results
        """
        pass

    @classmethod
    def is_multiargument(cls):
        # coooould be a property via metaclass
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

    def __call__(self):
        self.started = True
        while self.remaining:  # TODO: +retry behavior
            # this should come from client
            #print self.remaining
            cur_limit = min(self.remaining, PER_CALL_LIMIT)
            params = self.prepare_params(cur_limit,
                                         self.last_cont_str,
                                         **self.kwargs)
            resp = self.fetch(params)
            # TODO: check resp for api errors/warnings
            query_resp = resp.results.get(self.api_action)
            if not query_resp:
                print "that's an error: '%s'" % getattr(resp, 'url', '')
                continue
            try:
                new_results = self.extract_results(query_resp)
            except Exception:
                raise
            self.results.extend(new_results[:self.remaining])
            new_cont_str = self.get_cont_str(resp, params)
            if new_cont_str is None:
                break
            else:
                self.cont_strs.append(new_cont_str)

        return self.results


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
