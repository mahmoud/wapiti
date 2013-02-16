# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import QueryOperation, SingleParam, MultiParam, StaticParam
from models import PageIdentifier


class GetTranscludes(QueryOperation):
    # todo: namespaces
    param_prefix = 'gei'
    query_param = SingleParam('title', 'Template:')
    params = [StaticParam('generator', 'embeddedin'),
              StaticParam('prop', 'info'),
              StaticParam('inprop', 'title|pageid|ns|protection')]
    bijective = False

    def extract_results(self, query_resp):
        ret = []
        for k, pid_dict in query_resp.get('pages', {}).items():
            #if ns != 0 and to_zero_ns:  # non-Main/zero namespace
            #    try:
            #        _, _, title = pi['title'].partition(':')
            #        page_id = pi['subjectid']
            #        ns = 0
            #    except KeyError as e:
            #        continue  # TODO: log
            #else:
            try:
                page_ident = PageIdentifier.from_query(pid_dict, self.source)
            except ValueError:
                continue
            ret.append(page_ident)
        return ret
