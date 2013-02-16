# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import QueryOperation, StaticParam, MultiParam, SingleParam
from models import PageIdentifier, RevisionInfo, Revision

DEFAULT_PROPS = 'ids|flags|timestamp|user|userid|size|sha1|comment|tags'


class GetRevisionInfos(QueryOperation):
    """
    todo: switch to new data model (using unified PageIdentifiers)
    """
    param_prefix = 'rv'
    query_param = MultiParam('titles', key_prefix=False, required=True)
    params = [StaticParam('prop', 'revisions'),
              MultiParam('prop', DEFAULT_PROPS)]
    multiargument = False  # for now. it's not a big help in this case anyway.
    bijective = False

    def extract_results(self, query_resp):
        ret = []
        pages = [p for p in query_resp.get('pages', {}).values()
                 if 'missing' not in p]
        for pid_dict in pages:
            try:
                pid = PageIdentifier.from_query(pid_dict, self.source)
            except ValueError:
                continue
            if pid.page_id < 0:
                continue

            for rev in pid_dict.get('revisions', []):
                rev_info = RevisionInfo.from_query(pid, rev, self.source)
                ret.append(rev_info)
        return ret


class GetCurrentContent(QueryOperation):
    query_param = SingleParam('titles', key_prefix=False, required=True)
    param_prefix = 'rv'
    params = [StaticParam('prop', 'revisions'),
              MultiParam('prop', DEFAULT_PROPS + '|content'),
              SingleParam('parse', False),
              SingleParam('redirects', True, key_prefix=True)]
    bijective = True

    def prepare_params(self, *a, **kw):
        ret = super(GetCurrentContent, self).prepare_params(*a, **kw)
        return ret

    def extract_results(self, query_resp):
        ret = []
        #redirect_list = query_resp.get('redirects', [])
        #redirects = dict([(r['from'], r['to']) for r in redirect_list])
        requested_title = self.query_param
        is_parsed = self.kwargs.get('rvparse', False)

        pages = query_resp.get('pages', {})
        for pid_dict in pages.values():
            try:
                pid = PageIdentifier.from_query(pid_dict,
                                                self.source,
                                                requested_title)
            except ValueError:
                continue
            if pid.page_id < 0:
                continue
            rev = pid_dict['revisions'][0]
            revision = Revision.from_query(pid, rev, self.source, is_parsed)
            ret.append(revision)
        return ret


class GetCurrentTalkContent(GetCurrentContent):
    query_param = MultiParam('titles', 'Talk:', key_prefix=False, required=True)
