# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import QueryOperation, PageIdentifier, DEFAULT_RETRIES


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
