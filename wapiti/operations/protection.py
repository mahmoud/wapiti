# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import QueryOperation
from models import ProtectionInfo


class GetProtections(QueryOperation):
    param_prefix = 'in'
    query_param_name = 'titles'
    static_params = {'prop': 'info',
                     'inprop': 'protection'}

    def extract_results(self, query_resp):
        ret = []
        for page_id, page in query_resp['pages'].iteritems():
            ret.append(ProtectionInfo(page['protection']))
        return ret
