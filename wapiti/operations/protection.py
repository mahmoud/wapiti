# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import QueryOperation, SingleParam, MultiParam, StaticParam
from models import ProtectionInfo


class GetProtections(QueryOperation):
    field_prefix = 'in'
    query_field = MultiParam('titles', key_prefix=False, required=True)
    fields = [StaticParam('prop', 'langlinks'),
              SingleParam('prop', 'protection')]

    def extract_results(self, query_resp):
        ret = []
        for page_id, page in query_resp['pages'].iteritems():
            ret.append(ProtectionInfo(page['protection']))
        return ret
