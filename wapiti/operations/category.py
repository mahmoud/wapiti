# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from models import CategoryInfo, PageIdentifier, PageInfo
from base import (SubjectResolvingQueryOperation,
                  QueryOperation,
                  CompoundQueryOperation,
                  StaticParam,
                  SingleParam,
                  MultiParam)


class GetCategoryList(QueryOperation):
    field_prefix = 'gcl'
    query_field = MultiParam('titles', key_prefix=False, required=True)
    fields = [StaticParam('generator', 'categories'),
              StaticParam('prop', 'categoryinfo'),
              SingleParam('gclshow', ''),  # hidden, !hidden
              ]
    return_type = [CategoryInfo]

    def extract_results(self, query_resp):
        ret = []
        for k, pid_dict in query_resp['pages'].iteritems():
            try:
                cat_info = CategoryInfo.from_query(pid_dict,
                                                   source=self.source)
            except ValueError:
                print ValueError
                continue
            if cat_info.page_id < 0:
                continue
            ret.append(cat_info)
        return ret


class GetCategory(SubjectResolvingQueryOperation):
    field_prefix = 'gcm'
    query_field = SingleParam('title', val_prefix='Category:', required=True)
    fields = [StaticParam('generator', 'categorymembers'),
              StaticParam('prop', 'info'),
              StaticParam('inprop', 'subjectid|talkid|protection'),
              MultiParam('namespace', required=False)]
    return_type = [PageInfo]

    def extract_results(self, query_resp):
        ret = []
        for k, pid_dict in query_resp['pages'].iteritems():
            try:
                page_ident = PageInfo.from_query(pid_dict,
                                                 source=self.source)
            except ValueError:
                continue
            ret.append(page_ident)
        return ret


class GetCategoryPages(GetCategory):
    fields = GetCategory.fields + [StaticParam('gcmnamespace', '0|1')]


class GetSubcategoryInfos(QueryOperation):
    field_prefix = 'gcm'
    query_field = SingleParam('title', val_prefix='Category:', required=True)
    fields = [StaticParam('generator', 'categorymembers'),
              StaticParam('prop', 'categoryinfo'),
              StaticParam('gcmtype', 'subcat')]
    return_type = [CategoryInfo]

    def extract_results(self, query_resp):
        ret = []
        for k, pid_dict in query_resp['pages'].iteritems():
            try:
                pid_dict.update(pid_dict.get('categoryinfo', {}))
                cat_info = CategoryInfo.from_query(pid_dict,
                                                   source=self.source)
            except ValueError:
                continue
            if cat_info.page_id < 0:
                continue
            ret.append(cat_info)
        return ret


class GetAllCategoryInfos(GetSubcategoryInfos):
    field_prefix = 'gac'
    query_field = None
    fields = [StaticParam('generator', 'allcategories'),
              StaticParam('prop', 'categoryinfo')]

    def __init__(self, limit=10, **kw):
        super(GetAllCategoryInfos, self).__init__(None, limit, **kw)


class GetFlattenedCategory(CompoundQueryOperation):
    bijective = False
    multiargument = False

    suboperation_type = GetSubcategoryInfos

    def __init__(self, query_param, *a, **kw):
        super(GetFlattenedCategory, self).__init__(query_param, *a, **kw)
        self.seen_cat_names = set([query_param])

    def store_results(self, results):
        for cat_info in results:
            title = cat_info.title
            if title in self.seen_cat_names:
                continue
            self.seen_cat_names.add(title)
            self.results.append(cat_info)
            if cat_info.subcat_count:
                priority = cat_info.subcat_count
                subop = GetSubcategoryInfos(title, self)
                self.suboperations.add(subop, priority)
        return results


class GetCategoryRecursive(CompoundQueryOperation):
    bijective = False
    multiargument = False

    default_generator = GetFlattenedCategory
    suboperation_type = GetCategory
    suboperation_params = {'query_param': lambda ci: ci.title,
                           'priority': lambda ci: ci.page_count}

    def __init__(self, query_param, *a, **kw):
        super(GetCategoryRecursive, self).__init__(query_param, *a, **kw)
        self.seen_titles = set([query_param])

    def store_results(self, results):
        for page_ident in results:
            title = page_ident.title
            if title in self.seen_titles:
                continue
            self.seen_titles.add(title)
            self.results.append(page_ident)
        return results


class GetCategoryPagesRecursive(GetCategoryRecursive):
    suboperation_type = GetCategoryPages
