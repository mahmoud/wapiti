# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import QueryOperation, SingleParam, MultiParam, StaticParam
from models import PageIdentifier, LanguageLink, InterwikiLink


class GetBacklinks(QueryOperation):
    param_prefix = 'bl'
    query_param = SingleParam('title', prefix_key=False, required=True)
    params = [StaticParam('list', 'backlinks')]

    def extract_results(self, query_resp):
        ret = []
        for pid_dict in query_resp.get('backlinks', []):
            try:
                page_ident = PageIdentifier.from_query(pid_dict, self.source)
            except ValueError:
                continue
            ret.append(page_ident)
        return ret


class GetLanguageLinks(QueryOperation):
    param_prefix = 'll'
    query_param = MultiParam('titles', prefix_key=False, required=True)
    params = [StaticParam('prop', 'langlinks'),
              SingleParam('url', True)]

    def extract_results(self, query_resp):
        ret = []
        for pid_dict in query_resp.get('pages', {}).values():
            try:
                page_ident = PageIdentifier.from_query(pid_dict, self.source)
            except ValueError:
                continue
            for ld in pid_dict.get('langlinks', []):
                link = LanguageLink(ld.get('url'),
                                    ld.get('lang'),
                                    page_ident)
                ret.append(link)
        return ret


class GetInterwikiLinks(QueryOperation):
    param_prefix = 'iw'
    query_param = MultiParam('titles', prefix_key=False, required=True)
    params = [StaticParam('prop', 'iwlinks'),
              SingleParam('url', True)}

    def extract_results(self, query_resp):
        ret = []
        for pid_dict in query_resp.get('pages', {}).values():
            try:
                page_ident = PageIdentifier.from_query(pid_dict, self.source)
            except ValueError:
                continue
            for iwd in pid_dict.get('iwlinks', []):
                link = InterwikiLink(iwd.get('url'),
                                     iwd.get('prefix'),
                                     page_ident)
                ret.append(link)
        return ret
