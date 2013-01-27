# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import namedtuple

from base import QueryOperation, parse_timestamp

RevisionInfo = namedtuple('RevisionInfo', 'page_title, page_id, namespace, rev_id, rev_parent_id, user_text, user_id, length, time, sha1, comment, tags')


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
        pages = [ p for p in query_resp.get('pages', {}).values()
                  if 'missing' not in p ]
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
