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

'''
def get_revision_infos(page_title=None, page_id=None, limit=PER_CALL_LIMIT, cont_str=""):
    ret = []
    params = {'prop': 'revisions',
              'rvprop': 'ids|flags|timestamp|user|userid|size|sha1|comment|tags'}
    if page_title and page_id:
        raise ValueError('Expected one of page_title or page_id, not both.')
    elif page_title:
        params['titles'] = page_title
    elif page_id:
        params['pageids'] = str(page_id)
    else:
        raise ValueError('page_title and page_id cannot both be blank.')

    resps = []
    res_count = 0
    while res_count < limit and cont_str is not None:
        cur_limit = min(limit - len(ret), PER_CALL_LIMIT)
        params['rvlimit'] = cur_limit
        if cont_str:
            params['rvcontinue'] = cont_str
        resp = api_req('query', params)
        try:
            qresp = resp.results['query']
            resps.append(qresp)

            plist = qresp['pages'].values()  # TODO: uuuugghhhhh
            if plist and not plist[0].get('missing'):
                res_count += len(plist[0]['revisions'])
        except:
            #print resp.error  # log
            raise
        try:
            cont_str = resp.results['query-continue']['revisions']['rvcontinue']
        except:
            cont_str = None

    for resp in resps:
        plist = resp['pages'].values()
        if not plist or plist[0].get('missing'):
            continue
        else:
            page_dict = plist[0]
        page_title = page_dict['title']
        page_id = page_dict['pageid']
        namespace = page_dict['ns']

        for rev in page_dict.get('revisions', []):
            rev_info = RevisionInfo(page_title=page_title,
                                    page_id=page_id,
                                    namespace=namespace,
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
'''
