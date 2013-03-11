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


class MetaTypeWrapper(type):
    def __new__(mcls, name, reqd_kwargs=None):
        reqd_kwargs = reqd_kwargs or []
        wrapper = super(mcls, mcls).__new__(mcls,
                                            name,
                                            (TypeWrapper,),
                                            {'_reqd_kwargs': reqd_kwargs})
        return wrapper

    def __init__(cls, *a, **kw):
        super(MetaTypeWrapper, cls).__init__(cls.__name__,
                                             cls.__bases__,
                                             cls.__dict__)


class TypeWrapper(type):
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

        old_attrs = {}
        base_type = bases[0]
        if isinstance(base_type, TypeWrapper):
            for attr in base_type._wrapped_attrs:
                old_attrs[attr] = getattr(base_type, attr)
            base_type = base_type.__bases__[0]

        bases = (base_type,)
        base_name = base_type.__name__
        attrs['__module__'] = base_type.__module__
        ret = super(TypeWrapper, mcls).__new__(mcls, base_name, bases, attrs)
        ret._wrapped_attrs = set()

        for attr, val in old_attrs.items():
            setattr(ret, attr, val)
        return ret

    def __init__(mcls, to_wrap, **kw):
        for name in mcls._reqd_kwargs:
            try:
                val = kw.pop(name)
            except KeyError:
                msg = '%s expected keyword argument %r'
                raise TypeError(msg % (mcls.__name__, name))
            setattr(mcls, name, val)
        if kw:
            raise TypeError('%s got unexpected keyword arguments: %r'
                            % kw.keys())

    def __repr__(cls):
        wrapped_attr_map = dict([(k, getattr(cls, k, None))
                                 for k in cls._wrapped_attrs
                                 if k in cls.__dict__])
        kv = ', '.join(['%s=%r' % (k, v) for k, v in wrapped_attr_map.items()])
        tmpl = "<wrapped class '%s.%s' (%s)>"
        return  tmpl % (cls.__module__, cls.__name__, kv)

    def __setattr__(cls, name, val):
        super(TypeWrapper, cls).__setattr__(name, val)
        if not name == '_wrapped_attrs':
            cls._wrapped_attrs.add(name)

    def __delattr__(cls, name, val):
        super(TypeWrapper, cls).__delattr__(name, val)
        try:
            cls._wrapped_attrs.remove(name)
        except KeyError:
            pass


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

    def pop(self):
        while self._pq:
            priority, count, task = heappop(self._pq)
            if task is not REMOVED:
                del self._entry_map[task]
                return task
        raise KeyError('pop from an empty priority queue')

    def __len__(self):
        return len(self._entry_map)

    def __getitem__(self, index):
        # this is hacky! could make a sorted copy from the
        # heap and index into that at some point.
        if index != -1:
            raise IndexError('priority queues only support indexing on -1')
        _, _, task = self._pq[0]
        return task


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
