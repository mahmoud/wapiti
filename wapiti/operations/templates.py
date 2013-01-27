# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import PageIdentifier, QueryOperation


class GetTranscludes(QueryOperation):
    # todo: namespaces
    param_prefix = 'gei'
    query_param_name = param_prefix + 'title'
    query_param_prefix = 'Template:'
    static_params = {'generator': 'embeddedin',
                     'prop': 'info',
                     'inprop': 'title|pageid|ns|protection'}
    multiargument = False
    bijective = False

    def extract_results(self, query_resp):
        ret = []
        for k, pi in query_resp.get('pages', {}).items():
            if not pi.get('pageid'):
                continue
            ns = pi['ns']
            #if ns != 0 and to_zero_ns:  # non-Main/zero namespace
            #    try:
            #        _, _, title = pi['title'].partition(':')
            #        page_id = pi['subjectid']
            #        ns = 0
            #    except KeyError as e:
            #        continue  # TODO: log
            #else:
            title = pi['title']
            page_id = pi['pageid']
            ret.append(PageIdentifier(title=title,
                                      page_id=page_id,
                                      ns=ns,
                                      source=self.source))
        return ret
