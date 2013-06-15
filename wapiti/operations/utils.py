# -*- coding: utf-8 -*-

import sys
from heapq import heappush, heappop
import itertools
from functools import total_ordering


def is_scalar(obj):
    return not hasattr(obj, '__iter__') or isinstance(obj, basestring)


def prefixed(arg, prefix=None):
    if prefix and not arg.startswith(prefix):
        arg = prefix + arg
    return arg


@total_ordering
class MaxInt(long):
    """
    A quite-large integer type that tries to be like float('inf')
    (Infinity), but can be used for slicing and other integer
    operations. float('inf') is generally more correct, except that
    mixing a float and integer in arithmetic operations will result in
    a float, which will raise an error on slicing.
    """
    def __new__(cls, *a, **kw):
        return super(MaxInt, cls).__new__(cls, sys.maxint + 1)

    def __init__(self, name='MAX'):
        self._name = str(name)

    def __repr__(self):
        return self._name

    def __str__(self):
        return repr(self)

    # TODO: better math
    for func in ('__add__', '__sub__', '__mul__', '__floordiv__', '__div__',
                 '__mod__', '__divmod__', '__pow__', '__lshift__',
                 '__rshift__'):
        locals()[func] = lambda self, other: self

    def __gt__(self, other):
        return not self == other

    def __eq__(self, other):
        return isinstance(other, MaxInt)

    def __int__(self):
        return self


class OperationExample(object):
    """
    Sort of like a partial, but specialer.

    # other types of tests?
    """
    def __init__(self,
                 param=None,
                 limit=None,
                 op_type=None,
                 **kw):
        self.op_type = op_type
        self.param = param
        self.limit = limit

        self.doc = kw.pop('doc', '')
        self.test = kw.pop('test', None)
        # test defaults to limit_equal_or_depleted in test_ops.py
        if kw:
            raise TypeError('got unexpected keyword arguments: %r' % kw)

    @property
    def op_name(self):
        if self.op_type is None:
            return None
        return self.op_type.__name__

    @property
    def disp_name(self):
        if not self.op_type:
            return '(unbound OperationExample)'
        tmpl = '%(type)s(%(param)r, limit=%(limit)s)'
        if self.op_type.input_field is None:
            tmpl = '%(type)s(limit=%(limit)s)'

        return tmpl % {'type': self.op_type.__name__,
                       'param': self.param,
                       'limit': self.limit}

    def bind_op_type(self, op_type):
        if self.op_type is None:
            self.op_type = op_type
        if self.limit is None:
            try:
                pql = op_type.per_query_limit
            except AttributeError:
                pql = op_type.subop_chain[0].per_query_limit
            self.limit = pql.get_limit()
        return

    def make_op(self, mag=None):
        if not self.op_type:
            raise TypeError('no Operation type assigned')
        mag = int(mag or 1)
        limit = self.limit * mag
        if self.op_type.input_field is None:
            return self.op_type(limit=limit)
        return self.op_type(self.param, limit=limit)

    def __repr__(self):
        cn = self.__class__.__name__
        kwargs = ['param', 'limit', 'test', 'doc']
        kw_parts = ['op_type=%s' % self.op_name]
        vals = [getattr(self, a) for a in kwargs if getattr(self, a)]
        kw_parts.extend(['%s=%r' % (a, v) for a, v in zip(kwargs, vals)])
        kwarg_str = ', '.join(kw_parts)
        return '%s(%s)' % (cn, kwarg_str)

    __str__ = __repr__


"""
TypeWrapper and MetaTypeWrapper are a pair of what are technically
metaclasses, but really just a very overwrought way of enabling
customized versions of types floating around in some
locations. Because Wapiti is a DSL, but also just a bunch of Python,
we have to deal with the fact that if you modify a type/class, it will
be modified everywhere that references it.

TL;DR: This overblown thing lets Operations use something like
Prioritized(GetCategory, key='total_count'), which sets a priority for
better queueing, without modifying the GetCategory Operation
itself. (Different operations will want to prioritiez different
things.)

(There is almost certainly a better way, but this was a bit of
fun. Ever made an object that is an instance and a subclass of
itself?)
"""


def make_type_wrapper(name, init_args=None):
    init_args = init_args or []
    args, defaults = [], {}
    for ia in init_args:
        try:
            arg, _default = ia
            defaults[arg] = _default
        except ValueError:
            arg = ia
        if not isinstance(arg, basestring):
            raise TypeError('expected string arg name, not %r' % arg)
        args.append(arg)

    attrs = {'_args': args, '_defaults': defaults}
    return WrapperType(str(name), (Wrapper,), attrs)


class WrapperType(type):
    @property
    def _repr_args(self):
        ret = []
        for a in self._args:
            try:
                ret.append((a, self._defaults[a]))
            except KeyError:
                ret.append(a)
        return ret

    def __repr__(cls):
        name, cname = cls.__name__, cls.__class__.__name__
        if cls._repr_args:
            return '%s(%r, %r)' % (cname, name, cls._repr_args)
        else:
            return '%s(%r)' % (cname, name)


class Wrapper(object):
    __metaclass__ = WrapperType
    _args, _defaults = [], {}

    def __init__(self, to_wrap, *args, **kwargs):
        wrapped_dict = {}
        if isinstance(to_wrap, Wrapper):
            wrapped_dict = dict(to_wrap._wrapped_dict)
            to_wrap = to_wrap._wrapped
        self.__dict__['_wrapped'] = to_wrap
        self.__dict__['_wrapped_dict'] = wrapped_dict

        cn = self.__name__
        for arg_i, arg_name in enumerate(self._args):
            try:
                val = args[arg_i]
                if arg_name in kwargs:
                    raise TypeError('%s got multiple values for arg %r'
                                    % (cn, arg_name))
            except IndexError:
                try:
                    val = kwargs.pop(arg_name)
                except KeyError:
                    try:
                        val = self._defaults[arg_name]
                    except KeyError:
                        raise TypeError('%s expected required arg %r'
                                        % (cn, arg_name))
            setattr(self, arg_name, val)
        return

    def __repr__(self):
        kv = ', '.join(['%s=%r' % (k, v) for k, v
                        in self._wrapped_dict.items()])
        tmpl = "<wrapped %r (%s)>"
        return tmpl % (self._wrapped, kv)

    def __getattr__(self, name):
        return getattr(self._wrapped, name)

    def __setattr__(self, name, val):
        super(Wrapper, self).__setattr__(name, val)
        self._wrapped_dict[name] = val

    def __delattr__(self, name, val):
        super(Wrapper, self).__delattr__(name, val)
        self._wrapped_dict.pop(name, None)

    def __call__(self, *a, **kw):
        return self._wrapped(*a, **kw)


REMOVED = '<removed-task>'


class PriorityQueue(object):
    """
    Real quick type based on the heapq docs.
    """
    def __init__(self):
        self._pq = []
        self._entry_map = {}
        self.counter = itertools.count()

    def add(self, task, priority=None):
        # larger numbers = higher priority
        priority = -int(priority or 0)
        if task in self._entry_map:
            self.remove_task(task)
        count = next(self.counter)
        entry = [priority, count, task]
        self._entry_map[task] = entry
        heappush(self._pq, entry)

    def remove(self, task):
        entry = self._entry_map.pop(task)
        entry[-1] = REMOVED

    def _cull(self):
        while self._pq:
            priority, count, task = self._pq[0]
            if task is REMOVED:
                heappop(self._pq)
                continue
            return
        raise IndexError('empty priority queue')

    def peek(self, default=REMOVED):
        try:
            self._cull()
            _, _, task = self._pq[0]
        except IndexError:
            if default is not REMOVED:
                return default
            raise IndexError('peek on empty queue')
        return task

    def pop(self, default=REMOVED):
        try:
            self._cull()
            _, _, task = heappop(self._pq)
            del self._entry_map[task]
        except IndexError:
            if default is not REMOVED:
                return default
            raise IndexError('pop on empty queue')
        return task

    def __len__(self):
        return len(self._entry_map)


def chunked_iter(src, size, **kw):
    """
    Generates 'size'-sized chunks from 'src' iterable. Unless
    the optional 'fill' keyword argument is provided, iterables
    not even divisible by 'size' will have a final chunk that is
    smaller than 'size'.

    Note that fill=None will in fact use None as the fill value.

    >>> list(chunked_iter(range(10), 3))
    [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]
    >>> list(chunked_iter(range(10), 3, fill=None))
    [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9, None, None]]
    """
    size = int(size)
    if size <= 0:
        raise ValueError('expected a positive integer chunk size')
    do_fill = True
    try:
        fill_val = kw.pop('fill')
    except KeyError:
        do_fill = False
        fill_val = None
    if kw:
        raise ValueError('got unexpected keyword arguments: %r' % kw.keys())
    if not src:
        return
    cur_chunk = []
    i = 0
    for item in src:
        cur_chunk.append(item)
        i += 1
        if i % size == 0:
            yield cur_chunk
            cur_chunk = []
    if cur_chunk:
        if do_fill:
            lc = len(cur_chunk)
            cur_chunk[lc:] = [fill_val] * (size - lc)
        yield cur_chunk
    return

# From http://en.wikipedia.org/wiki/Wikipedia:Namespace
NAMESPACES = {
    'Main': 0,
    'Talk': 1,
    'User': 2,
    'User talk': 3,
    'Wikipedia': 4,
    'Wikipedia talk': 5,
    'File': 6,
    'File talk': 7,
    'MediaWiki': 8,
    'MediaWiki talk': 9,
    'Template': 10,
    'Template talk': 11,
    'Help': 12,
    'Help talk': 13,
    'Category': 14,
    'Category talk': 15,
    'Portal': 100,
    'Portal talk': 101,
    'Book': 108,
    'Book talk': 109,
    'Special': -1,
    'Media': -2}


def bucketize(src, keyfunc=None):
    """
    Group values in 'src' iterable by value returned by 'keyfunc'.
    keyfunc defaults to bool, which will group the values by
    truthiness; at most there will be two keys, True and False, and
    each key will have a list with at least one item.

    >>> bucketize(range(5))
    {False: [0], True: [1, 2, 3, 4]}
    >>> is_odd = lambda x: x % 2 == 1
    >>> bucketize(range(5), is_odd)
    {False: [0, 2, 4], True: [1, 3]}

    Value lists are not deduplicated:

    >>> bucketize([None, None, None, 'hello'])
    {False: [None, None, None], True: ['hello']}
    """
    if not is_iterable(src):
        raise TypeError('expected an iterable')
    if keyfunc is None:
        keyfunc = bool
    if not callable(keyfunc):
        raise TypeError('expected callable key function')

    ret = {}
    for val in src:
        key = keyfunc(val)
        ret.setdefault(key, []).append(val)
    return ret


def bucketize_bool(src, keyfunc=None):
    """
    Like bucketize, but for added convenience returns a tuple of
    (truthy_values, falsy_values).

    >>> nonempty, empty = bucketize_bool(['', '', 'hi', '', 'bye'])
    >>> nonempty
    ['hi', 'bye']

    keyfunc defaults to bool, but can be carefully overridden to
    use any function that returns either True or False.

    >>> import string
    >>> is_digit = lambda x: x in string.digits
    >>> decimal_digits, hexletters = bucketize_bool(string.hexdigits, is_digit)
    >>> ''.join(decimal_digits), ''.join(hexletters)
    ('0123456789', 'abcdefABCDEF')
    """
    bucketized = bucketize(src, keyfunc)
    return bucketized.get(True, []), bucketized.get(False, [])

def coerce_namespace(ns_arg):
    ns_str = str(ns_arg).capitalize()
    return NAMESPACES.get(ns_str, ns_str)
    