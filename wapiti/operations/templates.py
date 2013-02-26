# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import SubjectResolvingQueryOperation
from base import SingleParam, StaticParam
from models import PageInfo


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
                page_ident = PageInfo.from_query(pid_dict,
                                                       source=self.source)
            except ValueError:
                continue
            ret.append(page_ident)
        return ret


class GetAllTranscludes(GetTranscludes):
    field_prefix = 'gat'
    query_field = None
    fields = []
    fields = [StaticParam('generator', 'alltransclusions'),
              StaticParam('prop', 'imageinfo'),
              StaticParam('inprop', 'subjectid|talkid|protection')]

    def __init__(self, limit=10, **kw):
        super(GetAllTranscludes, self).__init__(None, limit, **kw)
