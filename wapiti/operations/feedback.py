# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import QueryOperation


class GetFeedbackV4(QueryOperation):
    param_prefix = 'af'
    query_param_name = param_prefix + 'pageid'
    static_params = {'list': 'articlefeedback'}

    def extract_results(self, query_resp):
        ret = query_resp['articlefeedback'][0].get('ratings', [])
        return ret


class GetFeedbackV5(QueryOperation):
    """
    article feedback v5 breaks standards in a couple ways.
      * the various v5 APIs use different prefixes (af/afvf)
      * it doesn't put its results under 'query', requiring a custom fetch()
    """
    param_prefix = 'afvf'
    query_param_name = param_prefix + 'pageid'
    static_params = {'list': 'articlefeedbackv5-view-feedback'}

    def fetch(self, params):
        tmp_resp = super(GetFeedbackV5, self).fetch(params)
        try:
            query_dict = dict(tmp_resp.results)
            tmp_resp.results['query'] = query_dict
        except TypeError:
            return tmp_resp
        return tmp_resp

    def extract_results(self, query_resp):
        count = query_resp['articlefeedbackv5-view-feedback']['count']
        return ['TODO'] * count
