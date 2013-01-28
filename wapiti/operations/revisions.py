# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import QueryOperation, parse_timestamp
from models import Page, RevisionInfo


class GetRevisionInfos(QueryOperation):
    """
    todo: switch to new data model (using unified PageIdentifiers)
    """
    param_prefix = 'rv'
    query_param_name = 'titles'
    static_params = {'prop': 'revisions',
                     'rvprop': 'ids|flags|timestamp|user|userid|size|sha1|comment|tags'}
    multiargument = False  # for now. it's not a big help in this case anyway.
    bijective = False

    def extract_results(self, query_resp):
        ret = []
        pages = [p for p in query_resp.get('pages', {}).values()
                 if 'missing' not in p]
        for page in pages:
            for rev in page.get('revisions', []):
                rev_info = RevisionInfo(page_title=page['title'],
                                        page_id=page['pageid'],
                                        namespace=page['ns'],
                                        rev_id=rev['revid'],
                                        rev_parent_id=rev['parentid'],
                                        user_text=rev.get('user', '!userhidden'),  # user info can be oversighted
                                        user_id=rev.get('userid', -1),
                                        time=parse_timestamp(rev['timestamp']),
                                        length=rev['size'],
                                        sha1=rev['sha1'],
                                        comment=rev.get('comment', ''),  # comments can also be oversighted
                                        tags=rev['tags'])
                ret.append(rev_info)
        return ret


class GetCurrentContent(QueryOperation):
    param_prefix = 'rv'
    query_param_name = 'titles'
    static_params = {'prop': 'revisions',
                     'rvprop': 'content|ids|contentmodel|sha1|size'}
    multiargument = False
    bijective = True

    def prepare_params(self, *a, **kw):
        ret = super(GetCurrentContent, self).prepare_params(*a, **kw)
        # TODO: better defaulting mechanism / dynamic argument handling
        if self.kwargs.get('rvparse', False):
            ret['rvparse'] = True
        if self.kwargs.get('redirects', True):
            ret['redirects'] = True
        return ret

    def extract_results(self, query_resp):
        ret = []
        #redirect_list = query_resp.get('redirects', [])
        #redirects = dict([(r['from'], r['to']) for r in redirect_list])

        pages = query_resp.get('pages', {})
        for pd in pages.values():
            title = pd['title']
            requested_title = self.query_param
            is_parsed = self.kwargs.get('rvparse', False)
            page = Page(title=title,
                        req_title=requested_title,
                        namespace=pd['ns'],
                        page_id=pd['pageid'],
                        rev_id=pd['revisions'][0]['revid'],
                        rev_text=pd['revisions'][0]['*'],
                        is_parsed=is_parsed)
            ret.append(page)
        return ret


class GetCurrentTalkContent(GetCurrentContent):
    query_param_prefix = 'Talk:'
