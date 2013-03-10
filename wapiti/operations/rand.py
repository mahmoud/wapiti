# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import QueryOperation
from params import StaticParam
from models import PageIdentifier


class GetRandom(QueryOperation):
    field_prefix = 'grn'
    fields = [StaticParam('generator', 'random'),
              StaticParam('prop', 'info'),
              StaticParam('inprop', 'subjectid|talkid|protection')]
    input_field = None
    output_type = [PageIdentifier]

    def extract_results(self, query_resp):
        ret = []
        for k, pid_dict in query_resp['pages'].iteritems():
            try:
                page_ident = PageIdentifier.from_query(pid_dict,
                                                       source=self.source)
            except ValueError:
                continue
            ret.append(page_ident)
        return ret

    def get_cont_str(self, *a, **kw):
        return ''
