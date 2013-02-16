# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import QueryOperation, SingleParam, MultiParam, StaticParam
from models import ProtectionInfo


class GetProtections(QueryOperation):
    param_prefix = 'in'
    query_param = MultiParam('titles', prefix_key=False, required=True)
    params = [StaticParam('prop', 'langlinks'),
              SingleParam('prop', 'protection')]

    def extract_results(self, query_resp):
        ret = []
        for page_id, page in query_resp['pages'].iteritems():
            ret.append(ProtectionInfo(page['protection']))
        return ret
