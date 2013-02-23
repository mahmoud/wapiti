# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import QueryOperation, SingleParam, MultiParam, StaticParam
from models import PageIdentifier, CoordinateIndentifier

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
                page_ident = PageIdentifier.from_query(pid_dict, self.source)
                for coord in pid_dict['coordinates']:
                    coord_ident = CoordinateIndentifier(coord, page_ident)
            except ValueError:
                continue
            ret.append(coord_ident)
        return ret


class GeoSearch(QueryOperation):
    field_prefix = 'gs'
    query_field = MultiParam('gscoord', key_prefix=False, required=True)
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
                page_ident = PageIdentifier.from_query(pid_dict, self.source)
                coord_ident = CoordinateIndentifier(pid_dict, page_ident)
            except ValueError:
                continue
            ret.append(coord_ident)
        return ret

'''

If we are completionists (for action=query)

* prop=imageinfo (ii) *
  Returns image information and upload history
* prop=info (in) *
  Get basic page information such as namespace, title, last touched date, ...
* prop=pageprops (pp) *
  Get various properties defined in the page content
* prop=templates (tl) *
  Returns all templates from the given page(s)
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
* list=allcategories (ac) *
  Enumerate all categories
* list=allimages (ai) *
  Enumerate all images sequentially
* list=alllinks (al) *
  Enumerate all links that point to a given namespace
* list=allpages (ap) *
  Enumerate all pages sequentially in a given namespace
* list=alltransclusions (at) *
  List all transclusions (pages embedded using {{x}}), including non-existing
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
* list=querypage (qp) *
  Get a list provided by a QueryPage-based special page
  qppage              - The name of the special page. Note, this is case sensitive
                        This parameter is required
                        One value: Ancientpages, BrokenRedirects, Deadendpages, Disambiguations, DoubleRedirects, Listredirects,
                            Lonelypages, Longpages, Mostcategories, Mostimages, Mostinterwikis, Mostlinkedcategories,
                            Mostlinkedtemplates, Mostlinked, Mostrevisions, Fewestrevisions, Shortpages,
                            Uncategorizedcategories, Uncategorizedpages, Uncategorizedimages, Uncategorizedtemplates,
                            Unusedcategories, Unusedimages, Wantedcategories, Wantedfiles, Wantedpages, Wantedtemplates,
                            Unwatchedpages, Unusedtemplates, Withoutinterwiki
* list=recentchanges (rc) *
  Enumerate recent changes
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
* meta=siteinfo (si) *
  Return general information about the site
'''