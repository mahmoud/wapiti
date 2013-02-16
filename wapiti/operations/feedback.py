# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import QueryOperation, SingleParam, StaticParam


class GetFeedbackV4(QueryOperation):
    field_prefix = 'af'
    query_field = SingleParam('pageid', required=True)
    fields = [StaticParam('list', 'articlefeedback')]

    def extract_results(self, query_resp):
        ret = query_resp['articlefeedback'][0].get('ratings', [])
        return ret


class GetFeedbackV5(QueryOperation):
    """
    article feedback v5 breaks standards in a couple ways.
      * the various v5 APIs use different prefixes (af/afvf)
      * it doesn't put its results under 'query', requiring a custom
      post_process_response()
    """
    field_prefix = 'afvf'
    query_field = SingleParam('pageid', required=True)
    fields = [StaticParam('list', 'articlefeedbackv5-view-feedback')]

    def post_process_response(self, response):
        if not response.results:
            return {}
        return dict(response.results)

    def extract_results(self, query_resp):
        count = query_resp['articlefeedbackv5-view-feedback']['count']
        return ['TODO'] * count
