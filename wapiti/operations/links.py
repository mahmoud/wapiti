# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import QueryOperation
from models import PageIdentifier, LanguageLink, InterwikiLink


class GetBacklinks(QueryOperation):
    param_prefix = 'bl'
    query_param_name = param_prefix + 'title'
    static_params = {'list': 'backlinks'}

    def extract_results(self, query_resp):
        ret = []
        for pid_dict in query_resp.get('backlinks', []):
            try:
                page_ident = PageIdentifier.from_query_result(pid_dict,
                                                              self.source)
            except ValueError:
                continue
            ret.append(page_ident)
        return ret


class GetLanguageLinks(QueryOperation):
    param_prefix = 'll'
    query_param_name = 'titles'
    static_params = {'prop': 'langlinks',
                     'llurl': 'true'}

    def extract_results(self, query_resp):
        ret = []
        for pid_dict in query_resp.get('pages', {}).values():
            try:
                page_ident = PageIdentifier.from_query_result(pid_dict,
                                                              self.source)
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
    query_param_name = 'titles'
    static_params = {'prop': 'iwlinks',
                     'iwurl': 'true'}

    def extract_results(self, query_resp):
        ret = []
        for pid_dict in query_resp.get('pages', {}).values():
            try:
                page_ident = PageIdentifier.from_query_result(pid_dict,
                                                              self.source)
            except ValueError:
                continue
            for iwd in pid_dict.get('iwlinks', []):
                link = InterwikiLink(iwd.get('url'),
                                     iwd.get('prefix'),
                                     page_ident)
                ret.append(link)
        return ret
