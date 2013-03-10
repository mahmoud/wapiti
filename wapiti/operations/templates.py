# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import QueryOperation, SingleParam, StaticParam
from models import PageInfo


class GetTranscludes(QueryOperation):
    input_field = SingleParam('title', val_prefix='Template:')
    field_prefix = 'gei'
    fields = [StaticParam('generator', 'embeddedin'),
              StaticParam('prop', 'info'),
              StaticParam('inprop', 'subjectid|talkid|protection')]
    output_type = [PageInfo]

    def extract_results(self, query_resp):
        ret = []
        for k, pid_dict in query_resp.get('pages', {}).items():
            try:
                page_ident = PageInfo.from_query(pid_dict,
                                                 source=self.source)
            except ValueError:
                continue
            ret.append(page_ident)
        return ret


class GetAllTranscludes(GetTranscludes):
    field_prefix = 'gat'
    input_field = None
    fields = [StaticParam('generator', 'alltransclusions'),
              StaticParam('prop', 'imageinfo'),
              StaticParam('inprop', 'subjectid|talkid|protection')]

    def __init__(self, limit=10, **kw):
        super(GetAllTranscludes, self).__init__(None, limit, **kw)
