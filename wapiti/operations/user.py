# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import QueryOperation, SingleParam, MultiParam, StaticParam
from models import PageIdentifier, LanguageLink, InterwikiLink, ExternalLink, RevisionInfo

DEFAULT_PROPS = 'ids|flags|timestamp|user|userid|size|sha1|comment|tags|title'


class GetUserContribs(QueryOperation):
    field_prefix = 'uc'
    query_field = SingleParam('user', required=True)
    fields = [StaticParam('list', 'usercontribs'),
              StaticParam('ucprop', DEFAULT_PROPS)]

    def extract_results(self, query_resp):
        ret = []
        for rev_dict in query_resp.get('usercontribs', []):
            if not rev_dict.get('parentid'):
                rev_dict['parentid'] = ''
            if not rev_dict.get('sha1'):
                rev_dict['sha1'] = ''
            try:
                page_ident = PageIdentifier.from_query(rev_dict, self.source)
                rev_ident = RevisionInfo.from_query(page_ident,
                                                rev_dict,
                                                self.source)
            except ValueError:
                continue
            ret.append(rev_ident)
        return ret

    def get_cont_str(self, resp, params):
        """
        list=usercontribs uses a different pattern for continue strings
        """
        qc_val = resp.results.get(self.api_action + '-continue')
        if qc_val is None:
            return None
        for key in ('generator', 'prop', 'list'):
            if key in params:
                next_key = params[key]
                break
        else:
            raise KeyError("couldn't find contstr")
        return qc_val[next_key]['ucstart']

    def prepare_params(self, **kw):
        params = dict(self.params)
        params[self.field_prefix + 'limit'] = self.current_limit
        if self.last_cont_str:
            params[self.field_prefix + 'start'] = self.last_cont_str
        return params
