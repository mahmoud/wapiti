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

from operations import ALL_OPERATIONS, DEFAULT_API_URL
from operations.params import StaticParam

DEFAULT_TIMEOUT = 15
import socket
socket.setdefaulttimeout(DEFAULT_TIMEOUT)  # TODO: better timeouts for reqs


_camel2under_re = re.compile('((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))')


def camel2under(string):
    return _camel2under_re.sub(r'_\1', string).lower()


def under2camel(string):
    return ''.join(w.capitalize() or '_' for w in string.split('_'))


class BoundOperation(object):  # TODO: Operation subtype?
    def __init__(self, op_type, client):
        self.client = client
        self.op_type = op_type
        self.op_inst = None

    def __call__(self, *a, **kw):
        if not self.op_inst:
            kw.setdefault('client', self.client)
            self.op_inst = self.op_type(*a, **kw)
            kw.pop('client')
        return self.op_inst()

    def __repr__(self):
        cn = self.__class__.__name__
        if self.op_inst:
            return '<%s %r bound to %r>' % (cn, self.op_inst, self.client)
        op_cn = self.op_type.__name__
        return '<%s %s bound to %r>' % (cn, op_cn, self.client)


class UnboundOperation(object):  # TODO: Operation subtype?
    def __init__(self, op_type):
        self.op_type = op_type

    def bind(self, client):
        return BoundOperation(self.op_type, client)

    def __get__(self, obj, obj_type=None):
        if obj_type and isinstance(obj, WapitiClient):
            return BoundOperation(self.op_type, obj)
        return self

    def __repr__(self):
        cn = self.__class__.__name__
        return '<%s %r>' % (cn, self.op_type)


class WapitiClient(object):
    """
    Provides logging, caching, settings, and a convenient interface
    to most (all?) operations.
    """
    def __init__(self,
                 user_email,
                 api_url=None,
                 is_bot=False,
                 init_source=True,
                 debug=False):
        # set settings obj
        # set up source (from api_url in settings)
        # then you're ready to call ops
        self.user_email = user_email
        self.api_url = api_url or DEFAULT_API_URL
        self.is_bot = is_bot
        self.debug = debug

        if init_source:
            self._init_source()

    def _init_source(self):
        # TODO: no input_field and single respones
        self.source_info = self.get_source_info()[0]

    @property
    def op_names(self):
        return list(sorted(self.op_map.keys()))

    def get_field_str(self, field):
        out_str = field.key
        mods = []
        if field.required:
            mods.append('required')
        if field.multi:
            mods.append('multi')
        if len(mods):
            out_str += ' (%s)' % ', '.join(mods)
        return out_str

    def print_op_usage(self, query=None):
        if query:
            op_names = [o for o in self.op_names if query.lower() in o.lower()]
        else:
            op_names = self.op_names

        for op_name in op_names:
            op = self.op_map[op_name]
            print op_name
            print 'INPUT:'
            if 'input_field' in dir(op) and op.input_field:
                print '\t%s' % self.get_field_str(op.input_field)
            else:
                print '\t(none)'

            print 'OPTIONS:'
            if 'fields' in dir(op):
                print_fields = [f for f in op.fields if not isinstance(f, StaticParam)]
                if len(print_fields):
                    for field in print_fields:
                        print '\t%s' % self.get_field_str(field)
                else:
                    print '\t(none)'
            else:
                print '\t(none)'

            print 'OUTPUT:'
            if 'output_type' in dir(op):
                print '\t%s' % repr(op.output_type)
            else:
                print '\t(none)'

            if 'examples' in dir(op):
                print 'EX:'
                print '\t%s' % ','.join([repr(x) for x in op.examples])

            print '\n'

    # TODO: configurable operations
    op_map = dict([(op.__name__, op) for op in ALL_OPERATIONS])
    unbound_op_map = dict([(camel2under(op_name), UnboundOperation(op))
                           for op_name, op in op_map.items()])
    unbound_op_set = set(unbound_op_map.values())
    locals().update(unbound_op_map)
