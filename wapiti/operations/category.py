# -*- coding: utf-8 -*-
"""
    wapiti.operations.category
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    A module of query operations related to categories. MediaWiki categories
    create an automatic index based on category tags in the page text.
"""
from __future__ import unicode_literals

from models import CategoryInfo, PageInfo
from base import (QueryOperation,
                  Operation,
                  Recursive)
from params import StaticParam, SingleParam, MultiParam


class GetCategoryList(QueryOperation):
    """
    Lists the categories for a page.
    """
    field_prefix = 'gcl'
    input_field = MultiParam('titles', key_prefix=False, required=True)
    fields = [StaticParam('generator', 'categories'),
              StaticParam('prop', 'categoryinfo'),
              SingleParam('gclshow', ''),  # hidden, !hidden
              ]
    output_type = [CategoryInfo]

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


class GetCategory(QueryOperation):
    """
    Lists the members in a category.
    """
    field_prefix = 'gcm'
    input_field = SingleParam('title', val_prefix='Category:', required=True)
    fields = [StaticParam('generator', 'categorymembers'),
              StaticParam('prop', 'info'),
              StaticParam('inprop', 'subjectid|talkid|protection'),
              MultiParam('namespace', required=False)]
    output_type = [PageInfo]

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
    """
    Lists the pages (namespace 0 or 1) in a category.
    """
    fields = GetCategory.fields + [StaticParam('gcmnamespace', '0|1')]


class GetSubcategoryInfos(QueryOperation):
    """
    The `CategoryInfo` for a category, which is useful to check the the number
    of members or sub-categories.
    """
    field_prefix = 'gcm'
    input_field = SingleParam('title', val_prefix='Category:', required=True)
    fields = [StaticParam('generator', 'categorymembers'),
              StaticParam('prop', 'categoryinfo'),
              StaticParam('gcmtype', 'subcat')]
    output_type = [CategoryInfo]

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
    """
    Lists all the categories on the wiki.
    """
    field_prefix = 'gac'
    input_field = None
    fields = [StaticParam('generator', 'allcategories'),
              StaticParam('prop', 'categoryinfo')]


class GetFlattenedCategory(Operation):
    """
    Lists all of a category's sub-categories.
    """
    subop_chain = Recursive(GetSubcategoryInfos)


class GetCategoryRecursive(Operation):
    """
    Lists all the members of a category and its sub-categories. A Wikipedia
    category tree can have a large number of shallow categories, so this
    operation will prioritize the larger categories by default.
    """
    subop_chain = (GetFlattenedCategory, GetCategory)


class GetCategoryPagesRecursive(GetCategoryRecursive):
    """
    Lists all the pages (namespace 0 and 1) in a category and its sub-
    categories.
    """
    subop_chain = (GetFlattenedCategory, GetCategoryPages)
