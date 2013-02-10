# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import deque
from base import QueryOperation, BaseQueryOperation, NoMoreResults, PriorityQueue
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

from functools import partial
class GetFlattenedCategory(BaseQueryOperation):
    bijective = False
    multiargument = False

    def __init__(self, query_param, *a, **kw):
        super(GetFlattenedCategory, self).__init__(query_param, *a, **kw)
        self.suboperations = PriorityQueue()
        root_subop = GetSubcategoryInfos(query_param, self.limit, owner=self)
        self.suboperations.add(root_subop)
        self.seen_cat_names = set([query_param])

    def get_current_task(self):
        if not self.remaining:
            return None
        while self.suboperations:
            subop = self.suboperations.pop()
            if subop.remaining:
                return partial(self.fetch_and_store, op=subop)
        return None

    def fetch_and_store(self, op=None):
        if op is None:
            if self.suboperations:
                op = self.suboperations.pop()
            else:
                return []
        try:
            res = op.process()
        except NoMoreResults:
            return []
        return self.store_results(res)

    def store_results(self, results):
        for cat_info in results:
            title = cat_info.title
            if title in self.seen_cat_names:
                continue
            self.seen_cat_names.add(title)
            self.results.append(cat_info)
            if cat_info.subcat_count:
                priority = -cat_info.subcat_count
                subop = GetSubcategoryInfos(title, self.limit, owner=self)
                self.suboperations.add(subop, priority)
        return results
