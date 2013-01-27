from __future__ import unicode_literals

from collections import namedtuple

'''
The beginnings of a better Mediawiki API library (with certain builtin
affordances for the more popular wikis and extensions). Most of what
you see below is implementation internals, the public API isn't set yet,
but check back soon.

# TODO
 * Create client class
 * Port more API calls
 * Support namespace filtering in a general fashion
 * Retry and timeout behaviors
 * Get my shit together and continue work on the HTTP client.
 * Automatically add 'g' to prefix if static_params has key 'generator'
 * Underscoring args
 * Support lists of static params (which are then joined automatically)
 * pause/resume
 * better differentiation between the following error groups:
   * Network/connectivity
   * Logic
   * Actual Mediawiki API errors ('no such category', etc.)
 * Relatedly: Save MediaWiki API warnings
'''


SOURCES = {'enwp': 'http://en.wikipedia.org/w/api.php'}
API_URL = SOURCES['enwp']  # TODO: hardcoded for nowskies
IS_BOT = False
DEFAULT_RETRIES = 0
DEFAULT_TIMEOUT  = 15
DEFAULT_HEADERS = { 'User-Agent': 'Loupe/0.0.0 Mahmoud Hashemi makuro@gmail.com' }

import socket
socket.setdefaulttimeout(DEFAULT_TIMEOUT)  # TODO: better timeouts for reqs

from ransom import Client
import json

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

# Protections
NEW = 2
AUTOCONFIRMED = 1
SYSOP = 0
Protection = namedtuple('Protection', 'level, expiry')
PROTECTION_ACTIONS = ['create', 'edit', 'move', 'upload']

def parse_timestamp(timestamp):
    return datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ')

class Permissions(object):
    """
    For more info on protection,
    see https://en.wikipedia.org/wiki/Wikipedia:Protection_policy
    """
    levels = {
        'new': NEW,
        'autoconfirmed': AUTOCONFIRMED,
        'sysop': SYSOP,
    }

    def __init__(self, protections=None):
        protections = protections or {}
        self.permissions = {}
        for p in protections:
            if p['expiry'] != 'infinity':
                expiry = parse_timestamp(p['expiry'])
            else:
                expiry = 'infinity'
            level = self.levels[p['level']]
            self.permissions[p['type']] = Protection(level, expiry)

    @property
    def has_protection(self):
        return any([x.level != NEW for x in self.permissions.values()])

    @property
    def has_indef(self):
        return any([x.expiry == 'infinity' for x in self.permissions.values()])

    @property
    def is_full_prot(self):
        try:
            if self.permissions['edit'].level == SYSOP and \
                    self.permissions['move'].level == SYSOP:
                return True
            else:
                return False
        except (KeyError, AttributeError):
            return False

    @property
    def is_semi_prot(self):
        try:
            if self.permissions['edit'].level == AUTOCONFIRMED:
                return True
            else:
                return False
        except (KeyError, AttributeError):
            return False


class WikiException(Exception):
    pass

BasePageIdentifier = namedtuple("PageIdentifier", "title, page_id, ns, source")


class PageIdentifier(BasePageIdentifier):
    pass


class CategoryInfo(PageIdentifier):
    def __init__(self, title, page_id, ns, source, total_count, page_count, file_count, subcat_count):
        super(CategoryInfo, self).__init__(title, page_id, ns, source)
        self.total_count = total_count
        self.page_count = page_count
        self.file_count = file_count
        self.subcat_count = subcat_count


#Page = namedtuple("Page", "title, req_title, namespace, page_id, rev_id, rev_text, is_parsed, fetch_date, fetch_duration")
#RevisionInfo = namedtuple('RevisionInfo', 'page_title, page_id, namespace, rev_id, rev_parent_id, user_text, user_id, length, time, sha1, comment, tags')


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


class QueryOperation(Operation):
    api_action = 'query'
    param_prefix = None        # e.g., 'gcm'
    query_param_name = None    # e.g., 'title'
    query_param_prefix = None  # e.g., 'Category:'

    def __init__(self, query_param, limit, namespaces=None, retries=DEFAULT_RETRIES, **kw):
        self.started = False
        self.cont_strs = []
        self.max_retries = retries
        self.retries = 0
        self.results = []

        self.query_param = query_param
        self.limit = limit
        self.namespaces = namespaces  # TODO: needs remapping/checking?
        self.kwargs = kw

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
        return self.limit - len(self.results)

    def prepare_params(self, limit, cont_str, **kw):
        params = dict(self.static_params)
        query_param_name = self.get_query_param_name()
        query_param = self.get_query_param()
        prefix = self.param_prefix
        if self.is_multi():
            query_param = join_multi_args(query_param, self.query_param_prefix)
        else:
            query_param = prefixed(query_param, self.query_param_prefix)
        #else:
        #    ensure_singular(query_param)
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
    def is_multi(cls):
        # coooould be a property via metaclass
        static_params = cls.static_params
        query_param_name = cls.query_param_name
        # TODO: some explicit way
        if 'prop' in static_params and 'generator' not in static_params:
            return False
        if 'list' in static_params:
            return False
        if query_param_name.endswith('title') or query_param_name.endswith('id'):
            # (change to "not query_param_name.endswith('s')"? )
            # singular argument name assumed to mean not multi
            return False

        return True

    def get_cont_str(self, resp, params):
        #todo? fuzzy walker thing to walk down to self.param_prefix+'continue'?
        tmp = resp.results[self.api_action + '-continue']
        for key in ('generator', 'prop', 'list'):
            if key in params:
                next_key = params[key]
                break
        else:
            raise KeyError("couldn't find contstr")
        return tmp[next_key][self.param_prefix + 'continue']


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
            query_resp = resp.results.get(self.api_action)
            if not query_resp:
                print "that's an error"
                continue
            try:
                new_results = self.extract_results(query_resp)
            except Exception:
                raise
            self.results.extend(new_results[:self.remaining])
            new_cont_str = self.get_cont_str(resp, params)
            self.cont_strs.append(new_cont_str)

        return self.results


class GetCategory(QueryOperation):
    param_prefix = 'gcm'
    query_param_name = param_prefix + 'title'
    query_param_prefix = 'Category:'
    static_params = {'generator': 'categorymembers',
                     'prop': 'info',
                     'inprop': 'title|pageid|ns|subjectid|protection'}


    def extract_results(self, query_resp):
        ret = []
        for k, cm in query_resp['pages'].iteritems():
            page_id = cm.get('pageid')
            if not page_id:
                continue
            ns = cm['ns']
            title = cm['title']
            ret.append(PageIdentifier(title=title,
                                      page_id=page_id,
                                      ns=ns,
                                      source=self.source))
        return ret


class GetRandom(QueryOperation):
    param_prefix = 'grn'
    static_params = {'generator': 'random',
                     'prop': 'info',
                     'inprop': 'subjectid|protection'}
    query_param_name = param_prefix + 'title'

    def __init__(self, limit, namespaces=None, retries=DEFAULT_RETRIES, **kw):
        # TODO: removed query arg parameter, random doesn't need it, but is
        # there a less ugly way?
        super(GetRandom, self).__init__(None, limit, namespaces, retries, **kw)

    def extract_results(self, query_resp):
        ret = []
        for k, cm in query_resp['pages'].iteritems():
            page_id = cm.get('pageid')
            if not page_id:
                continue
            ns = cm['ns']
            title = cm['title']
            ret.append(PageIdentifier(title=title,
                                      page_id=page_id,
                                      ns=ns,
                                      source=self.source))
        return ret

    def get_cont_str(self, *a, **kw):
        return ''


class GetSubcategoryInfos(QueryOperation):
    param_prefix = 'gcm'
    static_params = {'generator': 'categorymembers',
                     'prop': 'categoryinfo',
                     'gcmtype': 'subcat'}
    query_param_name = param_prefix + 'title'
    query_param_prefix = 'Category:'

    def extract_results(self, query_resp):
        ret = []
        for k, cm in query_resp['pages'].iteritems():
            if not cm.get('pageid') or k < 0:
                continue
            namespace = cm['ns']
            title = cm['title']
            page_id = cm['pageid']
            ci = cm.get('categoryinfo')
            if ci:
                size = ci['size']
                pages = ci['pages']
                files = ci['files']
                subcats = ci['subcats']
            else:
                size, pages, files, subcats = (0, 0, 0, 0)
            ret.append(CategoryInfo(title=title,
                                    page_id=page_id,
                                    ns=namespace,
                                    source=self.source,
                                    total_count=size,
                                    page_count=pages,
                                    file_count=files,
                                    subcat_count=subcats))
        return ret

from ransom import Response

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
