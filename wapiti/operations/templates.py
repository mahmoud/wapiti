# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import SubjectResolvingQueryOperation
from base import SingleParam, StaticParam
from models import PageIdentifier


class GetTranscludes(SubjectResolvingQueryOperation):
    query_field = SingleParam('title', val_prefix='Template:')
    field_prefix = 'gei'
    fields = [StaticParam('generator', 'embeddedin'),
              StaticParam('prop', 'info'),
              StaticParam('inprop', 'subjectid|talkid|protection')]
    bijective = False

    def extract_results(self, query_resp):
        ret = []
        for k, pid_dict in query_resp.get('pages', {}).items():
            try:
                page_ident = PageIdentifier.from_query(pid_dict, self.source)
            except ValueError:
                continue
            ret.append(page_ident)
        return ret
