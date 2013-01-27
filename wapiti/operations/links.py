# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import PageIdentifier, QueryOperation


class GetBacklinks(QueryOperation):
    param_prefix = 'bl'
    query_param_name = param_prefix + 'title'
    static_params = {'list': 'backlinks'}

    def extract_results(self, query_resp):
        ret = []
        for link in query_resp.get('backlinks', []):
            page_id = link.get('pageid')
            if not page_id:
                continue
            ns = link['ns']
            title = link['title']
            ret.append(PageIdentifier(title=title,
                                      page_id=page_id,
                                      ns=ns,
                                      source=self.source))
        return ret
