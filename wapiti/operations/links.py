# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import QueryOperation
from params import SingleParam, MultiParam, StaticParam
from models import PageIdentifier, LanguageLink, InterwikiLink, ExternalLink
from utils import OperationExample


class GetImages(QueryOperation):
    """
    Fetch the images embedded on pages.
    """
    field_prefix = 'gim'
    input_field = MultiParam('titles', key_prefix=False)
    fields = [StaticParam('generator', 'images'),
              StaticParam('prop', 'info')]
    output_type = [PageIdentifier]
    examples = [OperationExample('Coffee')]

    def extract_results(self, query_resp):
        ret = []
        for pid, pid_dict in query_resp['pages'].iteritems():
            if pid.startswith('-'):
                pid_dict['pageid'] = None  # TODO: breaks consistency :/
            try:
                page_ident = PageIdentifier.from_query(pid_dict,
                                                       source=self.source)
            except ValueError:
                continue
            ret.append(page_ident)
        return ret


class GetBacklinks(QueryOperation):
    """
    Fetch page's incoming links from other pages on source wiki.
    """
    field_prefix = 'bl'
    input_field = SingleParam('title')
    fields = [StaticParam('list', 'backlinks')]
    output_type = [PageIdentifier]
    examples = [OperationExample('Coffee')]

    def extract_results(self, query_resp):
        ret = []
        for pid_dict in query_resp.get('backlinks', []):
            page_ident = PageIdentifier.from_query(pid_dict,
                                                   source=self.source)
            ret.append(page_ident)
        return ret


class GetLinks(QueryOperation):
    """
    Fetch page's outgoing links to other pages on source wiki.
    """
    field_prefix = 'gpl'
    input_field = SingleParam('titles', key_prefix=False)
    fields = [StaticParam('generator', 'links'),
              StaticParam('prop', 'info'),
              MultiParam('namespace')]
    output_type = [PageIdentifier]
    examples = [OperationExample('Coffee')]

    def extract_results(self, query_resp):
        ret = []
        for k, pid_dict in query_resp['pages'].iteritems():
            page_ident = PageIdentifier.from_query(pid_dict,
                                                   source=self.source)
            ret.append(page_ident)
        return ret


class GetExternalLinks(QueryOperation):
    """
    Fetch page outgoing links to URLs outside of source wiki.
    """
    field_prefix = 'el'
    input_field = SingleParam('titles', key_prefix=False)
    fields = [StaticParam('prop', 'extlinks')]
    output_type = [ExternalLink]
    examples = [OperationExample('Croatian War of Independence')]

    def extract_results(self, query_resp):
        ret = []
        for pid_dict in query_resp.get('pages', {}).values():
            for el in pid_dict.get('extlinks', []):
                cur_dict = dict(pid_dict)
                cur_dict['source'] = self.source
                cur_dict['url'] = el.get('*')
                link = ExternalLink.from_query(cur_dict)
                ret.append(link)
        return ret

    def prepare_params(self, **kw):
        params = super(GetExternalLinks, self).prepare_params(**kw)
        if params.get('elcontinue'):
            params['eloffset'] = params.pop('elcontinue')
        return params


class GetLanguageLinks(QueryOperation):
    """
    Fetch pages' interlanguage links (aka "Language Links" in the MediaWiki
    API). Interlanguage links should correspond to pages on another language
    wiki. Mostly useful on a source wiki with a family of similar multilingual
    projects, such as Wikipedias.
    """
    field_prefix = 'll'
    input_field = MultiParam('titles', key_prefix=False)
    fields = [StaticParam('prop', 'langlinks'),
              SingleParam('url', True)]
    output_type = [LanguageLink]
    examples = [OperationExample('Coffee')]

    def extract_results(self, query_resp):
        ret = []
        for pid_dict in query_resp.get('pages', {}).values():
            for ld in pid_dict.get('langlinks', []):
                cur_dict = dict(pid_dict)
                cur_dict['source'] = self.source
                cur_dict['url'] = ld.get('*')
                cur_dict['language'] = ld.get('lang')
                link = LanguageLink.from_query(cur_dict)
                ret.append(link)
        return ret


class GetInterwikiLinks(QueryOperation):
    """
    Fetch pages' interwiki links.
    """
    field_prefix = 'iw'
    input_field = MultiParam('titles', key_prefix=False)
    fields = [StaticParam('prop', 'iwlinks'),
              SingleParam('url', True)]
    output_type = [InterwikiLink]
    examples = [OperationExample('Coffee')]

    def extract_results(self, query_resp):
        ret = []
        for pid_dict in query_resp.get('pages', {}).values():
            for iwd in pid_dict.get('iwlinks', []):
                cur_dict = dict(pid_dict)
                cur_dict['source'] = self.source
                cur_dict['url'] = iwd.get('url')
                cur_dict['prefix'] = iwd.get('prefix')
                link = InterwikiLink.from_query(cur_dict)
                ret.append(link)
        return ret
