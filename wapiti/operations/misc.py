# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import QueryOperation, SingleParam, MultiParam, StaticParam
from models import PageIdentifier, CoordinateIndentifier, PageInfo
from collections import namedtuple

# TODO: These operations should be moved to the proper file


class GetCoordinates(QueryOperation):
    field_prefix = ''
    query_field = MultiParam('titles', required=True)
    fields = [StaticParam('prop', 'coordinates'),
              SingleParam('coprimary', 'all'),  # primary, secondary, all
              MultiParam('coprop', 'type|name|dim|country|region')
              ]

    def extract_results(self, query_resp):
        ret = []
        for k, pid_dict in query_resp['pages'].iteritems():
            try:
                page_ident = PageIdentifier.from_query(pid_dict,
                                                       source=self.source)
                for coord in pid_dict['coordinates']:
                    coord_ident = CoordinateIndentifier(coord, page_ident)
            except ValueError:
                continue
            ret.append(coord_ident)
        return ret


class GeoSearch(QueryOperation):
    field_prefix = 'gs'
    query_field = MultiParam('coord', required=True)
    fields = [StaticParam('list', 'geosearch'),
              SingleParam('radius', 10000),  # must be within 10 and 10000
              #SingleParam('maxdim', 1000),  # does not work?
              SingleParam('globe', 'earth'),  # which planet? donno...
              SingleParam('namespace', required=False),
              StaticParam('gsprop', 'type|name|dim|country|region')
              ]

    def extract_results(self, query_resp):
        ret = []
        for pid_dict in query_resp['geosearch']:
            try:
                page_ident = PageIdentifier.from_query(pid_dict,
                                                       source=self.source)
                coord_ident = CoordinateIndentifier(pid_dict, page_ident)
            except ValueError:
                continue
            ret.append(coord_ident)
        return ret

DEFAULT_IMAGE_PROPS = 'timestamp|user|userid|comment|parsedcomment|url|size|dimensions|sha1|mime|thumbmime|mediatype|metadata|archivename|bitdepth'

class ImageInfo(PageIdentifier):
    attributes = {'image_repository': 'imagerepository',
                  'missing': 'missing',
                  'url': 'url',
                  'dimensions': 'dimensions',
                   'mime': 'mime',
                   'thumbmime': 'thumbmime',
                   'mediatype': 'mediatype',
                   'metadata': 'metadata',
                   'archivename': 'archivename',
                   'bitdepth': 'bitdepth'
                  }
    defaults = {'tags': '',
                'dimensions': '',
                'mime': '',
                'thumbmime': '',
                'mediatype': '',
                'metadata': '',
                'archivename': '',
                'bitdepth': '',
                'url': '',  # will only exist if imagerepository is not local
                'missing': False}

class GetImageInfos(QueryOperation):
    field_prefix = 'ii'
    query_field = MultiParam('titles', key_prefix=False, required=True)
    fields = [StaticParam('prop', 'imageinfo'),
              StaticParam('iiprop', DEFAULT_IMAGE_PROPS)]

    def extract_results(self, query_resp):
        ret = []
        for k, pid_dict in query_resp['pages'].iteritems():
            if int(k) < 0 and pid_dict['imagerepository'] != u'local':
                pid_dict['pageid'] = 'shared'
                pid_dict['revid'] = 'shared'
            try:
                pid_dict.update(pid_dict.get('imageinfo', [{}])[0])
                image_info = ImageInfo.from_query(pid_dict,
                                                       source=self.source)
            except ValueError as e:
                print e
                continue
            ret.append(image_info)
        return ret


class GetAllImageInfos(GetImageInfos):
    field_prefix = 'gai'
    query_field = None
    fields = []
    fields = [StaticParam('generator', 'allimages'),
              StaticParam('prop', 'imageinfo'),
              StaticParam('gaiprop', DEFAULT_IMAGE_PROPS)]

    def __init__(self, limit=10, **kw):
        super(GetAllImageInfos, self).__init__(None, limit, **kw)


class GetTemplates(QueryOperation):
    field_prefix = 'gtl'
    query_field = MultiParam('titles', key_prefix=False, required=True)
    fields = [StaticParam('generator', 'templates'),
              StaticParam('prop', 'info'),
              StaticParam('inprop', 'subjectid|talkid|protection')]

    def extract_results(self, query_resp):
        ret = []
        for k, pid_dict in query_resp['pages'].iteritems():
            try:
                page_ident = PageInfo.from_query(pid_dict,
                                                       source=self.source)
            except ValueError:
                continue
            ret.append(page_ident)
        return ret


class GetRecentChanges(QueryOperation):
    field_prefix = 'grc'
    query_field = None
    fields = [StaticParam('generator', 'recentchanges'),
              StaticParam('prop', 'info'),
              StaticParam('inprop', 'subjectid|talkid|protection')]

    def __init__(self, limit=500, **kw):
        super(GetRecentChanges, self).__init__(None, limit, **kw)

    def extract_results(self, query_resp):
        ret = []
        for k, pid_dict in query_resp['pages'].iteritems():
            try:
                page_ident = PageInfo.from_query(pid_dict,
                                                 source=self.source)
            except ValueError:
                continue
            ret.append(page_ident)
        return ret

    def prepare_params(self, **kw):
        params = super(GetRecentChanges, self).prepare_params(**kw)
        if params.get('qpcontinue'):
            params['grcstart'] = params.pop('grccontinue')
        return params

QueryPageInfo = namedtuple('QueryPageInfo', 'title ns value querypage cache')


class GetQueryPage(QueryOperation):
    field_prefix = 'qp'
    query_field = SingleParam('page', required=True)
    fields = [StaticParam('list', 'querypage')]
    acceptable_qps = ['Ancientpages',
                      'BrokenRedirects',
                      'Deadendpages',
                      'Disambiguations',
                      'DoubleRedirects',
                      'Listredirects',
                      'Lonelypages',
                      'Longpages',
                      'Mostcategories',
                      'Mostimages',
                      'Mostinterwikis',
                      'Mostlinkedcategories',
                      'Mostlinkedtemplates',
                      'Mostlinked',
                      'Mostrevisions',
                      'Fewestrevisions',
                      'Shortpages',
                      'Uncategorizedcategories',
                      'Uncategorizedpages',
                      'Uncategorizedimages',
                      'Uncategorizedtemplates',
                      'Unusedcategories',
                      'Unusedimages',
                      'Wantedcategories',
                      'Wantedfiles',
                      'Wantedpages',
                      'Wantedtemplates',
                      'Unwatchedpages',  # requires logging in
                      'Unusedtemplates',
                      'Withoutinterwiki']

    def __init__(self, qp, *a, **kw):
        if qp not in self.acceptable_qps:
          raise ValueError('Unrecognized query page: %r' % qp)
        return super(GetQueryPage, self).__init__(qp, *a, **kw)


    def extract_results(self, query_resp):
        ret = []
        cached = query_resp['querypage'].get('cachedtimestamp')
        name = query_resp['querypage'].get('name')
        for p in query_resp['querypage']['results']:
            page = QueryPageInfo(p['title'],
                                 p['ns'],
                                 p['value'],
                                 name,
                                 cached)
            ret.append(page)
        return ret

    def prepare_params(self, **kw):
        params = super(GetQueryPage, self).prepare_params(**kw)
        if params.get('qpcontinue'):
            params['qpoffset'] = params.pop('qpcontinue')
        return params

'''
If we are completionists (for action=query)

* prop=pageprops (pp) *
  Get various properties defined in the page content
* prop=videoinfo (vi) *
  Extends imageinfo to include video source information
* prop=transcodestatus *
  Get transcode status for a given file page
* prop=globalusage (gu) *
  Returns global image usage for a certain image
* prop=extracts (ex) *
  Returns plain-text or limited HTML extracts of the given page(s)
* prop=pageimages (pi) *
  Returns information about images on the page such as thumbnail and presence of photos.
* prop=flagged *
  Get information about the flagging status of the given pages.

* list=alllinks (al) *
  Enumerate all links that point to a given namespace
* list=allpages (ap) *
  Enumerate all pages sequentially in a given namespace
* list=allusers (au) *
  Enumerate all registered users
* list=blocks (bk) *
  List all blocked users and IP addresses

* list=exturlusage (eu) *
  Enumerate pages that contain a given URL
* list=filearchive (fa) *
  Enumerate all deleted files sequentially
* list=iwbacklinks (iwbl) *
  Find all pages that link to the given interwiki link.
* list=langbacklinks (lbl) *
  Find all pages that link to the given language link.

* list=logevents (le) *
  Get events from logs
* list=protectedtitles (pt) *
  List all titles protected from creation


* list=search (sr) *
  Perform a full text search
* list=tags (tg) *
  List change tags
* list=usercontribs (uc) *
  Get all edits by a user
* list=users (us) *
  Get information about a list of users
* list=abuselog (afl) *
  Show events that were caught by one of the abuse filters.
* list=abusefilters (abf) *
  Show details of the abuse filters.

'''
