# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import namedtuple

from base import QueryOperation, parse_timestamp

# Protections
NEW = 'NEW'
AUTOCONFIRMED = 'AUTOCONFIRMED'
SYSOP = 'SYSOP'
PROTECTION_ACTIONS = ('create', 'edit', 'move', 'upload')


Protection = namedtuple('Protection', 'level, expiry')

class ProtectionInfo(object):
    # TODO: turn into mixin, add to PageIdentifier
    """
    For more info on protection,
    see https://en.wikipedia.org/wiki/Wikipedia:Protection_policy
    """
    levels = {
        'new': NEW,
        'autoconfirmed': AUTOCONFIRMED,
        'sysop': SYSOP,
    }

    def __init__(self, protections, page_ident=None):
        self.page_ident = page_ident

        protections = protections or {}
        self.protections = {}
        for p in protections:
            if not p['expiry'] == 'infinity':
                expiry = parse_timestamp(p['expiry'])
            else:
                expiry = 'infinity'
            level = self.levels[p['level']]
            self.protections[p['type']] = Protection(level, expiry)

    @property
    def has_protection(self):
        return any([x.level != NEW for x in self.protections.values()])

    @property
    def has_indef(self):
        return any([x.expiry == 'infinity' for x in self.protections.values()])

    @property
    def is_full_prot(self):
        try:
            if self.protections['edit'].level == SYSOP and \
                    self.protections['move'].level == SYSOP:
                return True
            else:
                return False
        except (KeyError, AttributeError):
            return False

    @property
    def is_semi_prot(self):
        try:
            if self.protections['edit'].level == AUTOCONFIRMED:
                return True
            else:
                return False
        except (KeyError, AttributeError):
            return False

    def __repr__(self):
        return u'ProtectionInfo(%r)' % self.protections


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
