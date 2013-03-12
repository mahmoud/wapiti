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
    def __init__(self, input_param=None, limit=None, test=None):
        self.input_param = input_param
        if test is None:
            test = bool
        self.test = test


def len_eq(length):
    def test_len_eq(other):
        return len(other) == length
    return test_len_eq

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
    return TypeWrapperType(str(name), (TypeWrapper,), attrs)


class TypeWrapperType(type):
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


class TypeWrapper(type):
    __metaclass__ = TypeWrapperType
    _args, _defaults = [], {}

    def __new__(mcls, name_or_type, bases=None, attrs=None, **kw):
        nort = name_or_type
        attrs = attrs or {}
        if bases is None:
            if not isinstance(nort, type):
                raise TypeError('expected type, not %r' % nort)
            bases = (nort,)

        if len(bases) > 1:
            raise TypeError('TypeWrapper wraps a single type, not %r' % bases)
        elif not bases:
            raise TypeError('cannot create wrapped types without base type')

        wrapped_attr_dict = {}
        base_type = bases[0]
        if isinstance(base_type, TypeWrapper):
            wrapped_attr_dict = dict(base_type._wrapped_dict)
            base_type = base_type.__bases__[0]

        bases = (base_type,)
        base_name = str(base_type.__name__)
        attrs['__module__'] = base_type.__module__
        attrs['_wrapped_dict'] = {}
        ret = type.__new__(mcls, base_name, bases, attrs)

        for attr, val in wrapped_attr_dict.items():
            setattr(ret, attr, val)
        return ret

    def __init__(self, to_wrap, *args, **kwargs):
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
        if kwargs:
            raise TypeError('%s got unexpected keyword arguments: %r'
                            % (cn, kwargs.keys()))

    @property
    def _wrapped_type(self):
        return self.__bases__[0]

    def __repr__(self):
        kv = ', '.join(['%s=%r' % (k, v) for k, v
                        in self._wrapped_dict.items()])
        tmpl = "<wrapped class '%s.%s' (%s)>"
        return tmpl % (self.__module__, self.__name__, kv)

    def __setattr__(cls, name, val):
        super(TypeWrapper, cls).__setattr__(name, val)
        cls._wrapped_dict[name] = val

    def __delattr__(cls, name, val):
        super(TypeWrapper, cls).__delattr__(name, val)
        cls._wrapped_dict.pop(name, None)


#class Recursive(TypeWrapper):
#    def __init__(self, *a, **kw):
#        super(Recursive, self).__init__(*a, **kw)
#        self.is_recursive = True

"""
class _SentinelMeta(type):
    def __new__(cls, name, bases, attrs):
        pass

def make_sentinel(name):
    return _SentinelMeta(str(name), (object,), {})
"""

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

    def pop(self, default=REMOVED):
        try:
            task = self.peek()
            heappop(self._pq)
            del self._entry_map[task]
        except IndexError:
            if default is REMOVED:
                raise
            return default
        return task

    def __len__(self):
        return len(self._entry_map)

    def peek(self, default=REMOVED):
        while self._pq:
            priority, count, task = self._pq[0]
            if task is REMOVED:
                heappop(self._pq)
            else:
                return task
        if default is not REMOVED:
            return default
        raise IndexError('priority queue is empty')


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
