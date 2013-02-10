# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import deque
from base import QueryOperation, BaseQueryOperation, NoMoreResults
from models import CategoryInfo, PageIdentifier


class GetCategory(QueryOperation):
    param_prefix = 'gcm'
    query_param_name = param_prefix + 'title'
    query_param_prefix = 'Category:'
    static_params = {'generator': 'categorymembers',
                     'prop': 'info',
                     'inprop': 'title|pageid|ns|subjectid|protection'}

    def extract_results(self, query_resp):
        ret = []
        for k, pid_dict in query_resp['pages'].iteritems():
            try:
                page_ident = PageIdentifier.from_query(pid_dict, self.source)
            except ValueError:
                continue
            ret.append(page_ident)
        return ret


class GetSubcategoryInfos(QueryOperation):
    param_prefix = 'gcm'
    static_params = {'generator': 'categorymembers',
                     'prop': 'categoryinfo',
                     'gcmtype': 'subcat'}
    query_param_name = param_prefix + 'title'
    query_param_prefix = 'Category:'

    def extract_results(self, query_resp):
        ret = []
        for k, pid_dict in query_resp['pages'].iteritems():
            try:
                cat_info = CategoryInfo.from_query(pid_dict, self.source)
            except ValueError:
                continue
            if cat_info.page_id < 0:
                continue
            ret.append(cat_info)
        return ret


class GetFlattenedCategory(BaseQueryOperation):
    bijective = False
    multiargument = False

    def __init__(self, query_param, *a, **kw):
        super(GetFlattenedCategory, self).__init__(query_param, *a, **kw)
        self.suboperations = [GetSubcategoryInfos(query_param, owner=self)]
        self.seen_cat_names = set([query_param])

    def get_current_task(self):
        if not self.remaining:
            return None
        while self.suboperations:
            subop = self.suboperations[-1]
            if subop.remaining:
                return self.fetch_and_store
            else:
                self.suboperations.pop()
        return None

    def fetch_and_store(self):
        subop = self.suboperations[-1]
        try:
            res = subop.process()
        except NoMoreResults:
            return []
        self.store_results(res)

    def store_results(self, results):
        for cat_info in results:
            if cat_info.title in self.seen_cat_names:
                continue
            self.seen_cat_names.add(cat_info.title)
            self.results.append(cat_info)
            if cat_info.subcat_count:
                self.suboperations.append(GetSubcategoryInfos(cat_info.title, owner=self))
        return
