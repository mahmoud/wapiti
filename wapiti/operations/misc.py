# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import namedtuple

from base import QueryOperation
from params import SingleParam, MultiParam, StaticParam
from models import PageIdentifier, CoordinateIdentifier, PageInfo
from utils import OperationExample

# TODO: These operations should be moved to the proper file
# TODO: convert to real model(s)
QueryPageInfo = namedtuple('QueryPageInfo', 'title ns value querypage cache')

DEFAULT_COORD_PROPS = ['type', 'name', 'dim', 'country', 'region']


class GetPageInfo(QueryOperation):
    field_prefix = 'in'
    input_field = MultiParam('titles', key_prefix=False)
    fields = [StaticParam('prop', 'info'),
              MultiParam('prop', 'subjectid|talkid|protection')]
    output_type = PageInfo
    examples = [OperationExample(['Coffee', 'Category:Africa'])]

    def extract_results(self, query_resp):
        ret = []
        for k, pid_dict in query_resp['pages'].iteritems():
            try:
                page_info = PageInfo.from_query(pid_dict,
                                                source=self.source)
            except ValueError:
                continue
            ret.append(page_info)
        return ret


class GetCoordinates(QueryOperation):
    field_prefix = 'co'
    input_field = MultiParam('titles', key_prefix=False)
    fields = [StaticParam('prop', 'coordinates'),
              SingleParam('primary', 'all'),  # primary, secondary, all
              MultiParam('prop', DEFAULT_COORD_PROPS)]
    output_type = [CoordinateIdentifier]
    examples = [OperationExample(['White House', 'Mount Everest'])]

    def extract_results(self, query_resp):
        ret = []
        for k, pid_dict in query_resp['pages'].iteritems():
            try:
                page_ident = PageIdentifier.from_query(pid_dict,
                                                       source=self.source)
                for coord in pid_dict['coordinates']:
                    coord_ident = CoordinateIdentifier(coord, page_ident)
            except ValueError:
                continue
            ret.append(coord_ident)
        return ret


class GeoSearch(QueryOperation):
    field_prefix = 'gs'
    input_field = MultiParam('coord')
    fields = [StaticParam('list', 'geosearch'),
              SingleParam('radius', 10000),  # must be within 10 and 10000
              #SingleParam('maxdim', 1000),  # does not work?
              SingleParam('globe', 'earth'),  # which planet? donno...
              SingleParam('namespace'),
              StaticParam('gsprop', DEFAULT_COORD_PROPS)]
    output_type = [CoordinateIdentifier]
    examples = [OperationExample(('37.8197', '-122.479'), 1)]

    def extract_results(self, query_resp):
        ret = []
        for pid_dict in query_resp['geosearch']:
            try:
                page_ident = PageIdentifier.from_query(pid_dict,
                                                       source=self.source)
                coord_ident = CoordinateIdentifier(pid_dict, page_ident)
            except ValueError:
                continue
            ret.append(coord_ident)
        return ret


class GetRecentChanges(QueryOperation):
    field_prefix = 'grc'
    input_field = None
    fields = [StaticParam('generator', 'recentchanges'),
              StaticParam('prop', 'info'),
              StaticParam('inprop', 'subjectid|talkid|protection')]
    output_type = [PageInfo]
    examples = [OperationExample()]

    def extract_results(self, query_resp):
        ret = []
        for pid, pid_dict in query_resp['pages'].iteritems():
            if pid.startswith('-'):
                continue
            try:
                page_ident = PageInfo.from_query(pid_dict,
                                                 source=self.source)
            except ValueError:
                continue
            ret.append(page_ident)
        return ret

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
* list=users (us) *
  Get information about a list of users
* list=abuselog (afl) *
  Show events that were caught by one of the abuse filters.
* list=abusefilters (abf) *
  Show details of the abuse filters.

'''
