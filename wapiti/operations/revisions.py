# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import QueryOperation, StaticParam, MultiParam, SingleParam
from models import PageIdentifier, RevisionInfo, Revision


DEFAULT_PROPS = 'ids|flags|timestamp|user|userid|size|sha1|comment|parsedcomment|tags'


class GetPageRevisionInfos(QueryOperation):
    """
    todo: switch to new data model (using unified PageIdentifiers)
    """
    field_prefix = 'rv'
    input_field = MultiParam('titles', key_prefix=False, required=True)
    fields = [StaticParam('prop', 'revisions'),
              MultiParam('prop', DEFAULT_PROPS)]
    output_type = [RevisionInfo]

    def extract_results(self, query_resp):
        ret = []
        pages = [p for p in query_resp.get('pages', {}).values()
                 if 'missing' not in p]
        for pid_dict in pages:
            for rev in pid_dict.get('revisions', []):
                rev_dict = dict(pid_dict)
                rev_dict.update(rev)
                rev_info = RevisionInfo.from_query(rev_dict,
                                                   source=self.source)
                ret.append(rev_info)
        return ret


class GetRevisionInfos(GetPageRevisionInfos):
    input_field = MultiParam('revids', key_prefix=False, required=True)
    output_type = RevisionInfo

    def prepare_params(self, *a, **kw):
        ret = super(GetRevisionInfos, self).prepare_params()
        ret.pop(self.field_prefix + 'limit', None)
        return ret


class GetCurrentContent(QueryOperation):
    input_field = SingleParam('titles', key_prefix=False, attr='title', required=True)
    field_prefix = 'rv'
    fields = [StaticParam('prop', 'revisions'),
              MultiParam('prop', DEFAULT_PROPS + '|content'),
              SingleParam('parse', False),
              SingleParam('redirects', True, key_prefix=False)]
    output_type = Revision

    def extract_results(self, query_resp):
        ret = []
        #redirect_list = query_resp.get('redirects', [])  # TODO
        #redirects = dict([(r['from'], r['to']) for r in redirect_list])
        requested_title = self.query_param
        is_parsed = self.kwargs.get('rvparse', False)

        pages = query_resp.get('pages', {})
        for page_id, pid_dict in pages.iteritems():
            if page_id < 0:
                continue
            rev_dict = dict(pid_dict)
            rev_dict.update(pid_dict['revisions'][0])
            revision = Revision.from_query(rev_dict,
                                           source=self.source,
                                           is_parsed=is_parsed)
            revision.req_title = requested_title
            ret.append(revision)
        return ret


class GetCurrentTalkContent(GetCurrentContent):
    input_field = MultiParam('titles',
                             val_prefix='Talk:',
                             key_prefix=False,
                             required=True)
