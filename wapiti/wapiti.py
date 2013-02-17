# -*- coding: utf-8 -*-
from __future__ import unicode_literals


'''
The beginnings of a better Mediawiki API library (with certain builtin
affordances for the more popular wikis and extensions). Most of what
you see below is implementation internals, the public API isn't set yet,
but check back soon.

# TODO
 * Create client class
 * Port more API calls
 * Retry and timeout behaviors
 * Get my shit together and continue work on the HTTP client.
 * Underscoring args
 * pause/resume
 * better differentiation between the following error groups:
   * Network/connectivity
   * Logic
   * Actual Mediawiki API errors ('no such category', etc.)
 * Relatedly: Save MediaWiki API warnings

Types of API calls:
 * single argument -> multiple results (get category)
 * many arguments -> up to one result per argument (get protections)
 * multiple arguments -> multiple results per argument (get language links)
   * TODO: establish return format convention for this

Need generic support for:
 * APIs which support both pageid and title lookup
 * Redirect following
'''
import re
from functools import partial
from operations import ALL_OPERATIONS


_camel2under_re = re.compile('((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))')


def camel2under(string):
    return _camel2under_re.sub(r'_\1', string).lower()


def under2camel(string):
    return ''.join(w.capitalize() or '_' for w in string.split('_'))


class WapitiClient(object):
    """
    Provides logging, caching, settings, and a convenient interface
    to most (all?) operations.
    """
    def __init__(self):
        # set settings obj
        # set up source (from api_url in settings)
        # then you're ready to call ops
        self.api_url = None
        self.user_agent = None
        self.timeout = 15
        self.is_bot = False
        self.per_call_limit = 500
        self.retry_limit = 5

        self.source = None

        self._create_ops()

    def call_operation(self, op_type, *a, **kw):
        kw['client'] = self
        operation = op_type(*a, **kw)
        # TODO: add to queue or somesuch
        return operation()

    def _create_ops(self):
        for op in ALL_OPERATIONS:  # TODO
            func_name = camel2under(op.__name__)
            call_op = partial(self.call_operation, op)
            setattr(self, func_name, call_op)
