# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import QueryOperation
from params import MultiParam, StaticParam
from models import ProtectionInfo
from utils import OperationExample


class GetProtections(QueryOperation):
    field_prefix = 'in'
    input_field = MultiParam('titles', key_prefix=False)
    fields = [StaticParam('prop', 'info'),
              StaticParam('inprop', 'protection')]
    output_type = ProtectionInfo
    examples = [OperationExample('Coffee'),
                OperationExample('Coffee|House'),
                OperationExample(['Coffee', 'House'])]

    def extract_results(self, query_resp):
        ret = []
        for page_id, page in query_resp['pages'].iteritems():
            ret.append(ProtectionInfo(page['protection']))
        return ret
