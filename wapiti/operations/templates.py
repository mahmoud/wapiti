# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import QueryOperation
from params import SingleParam, StaticParam
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
                import pdb;pdb.set_trace()
            except ValueError:
                continue
            ret.append(page_ident)
        return ret


class GetAllTranscludes(GetTranscludes):
    field_prefix = 'at'
    input_field = None
    fields = [StaticParam('list', 'alltransclusions'),
              #StaticParam('prop', 'info'),
              StaticParam('atprop', 'ids|title')] # 'subjectid|talkid|protection')]
