# -*- coding: utf-8 -*-

from heapq import heappush, heappop
import itertools


def is_scalar(obj):
    return not hasattr(obj, '__iter__') or isinstance(obj, basestring)


def prefixed(arg, prefix=None):
    if prefix and not arg.startswith(prefix):
        arg = prefix + arg
    return arg


class TypeWrapper(type):
    def __new__(mcls, name_or_type, bases=None, attrs=None):
        attrs = attrs or {}
        if bases is None:
            if not isinstance(name_or_type, type):
                raise TypeError('expected type, not %r' % name_or_type)
            bases = (name_or_type,)

        if len(bases) > 1:
            raise TypeError('type wrappers wrap a single type, not %r' % bases)
        elif not bases:
            raise TypeError('cannot create wrapped types without base type')
        base_type = bases[0]
        base_name = base_type.__name__
        if isinstance(base_type, TypeWrapper):
            raise TypeError('attempted to subclass a wrapped type: %s' % name)

        ret = super(TypeWrapper, mcls).__new__(mcls, base_name, bases, attrs)
        ret._wrapped_attrs = set()
        ret.__module__ = base_type.__module__
        return ret

    def get_unwrapped(cls):
        return cls.__bases__[0]

    @classmethod
    def __setattr__(cls, name, val):
        super(TypeWrapper, cls).__setattr__(cls, name, val)
        if not name == '_wrapped_attrs':
            cls._wrapped_attrs.add(name)

    @classmethod
    def __delattr__(cls, name, val):
        super(TypeWrapper, cls).__delattr__(name, val)
        try:
            cls._wrapped_attrs.remove(name)
        except KeyError:
            pass

    @classmethod
    def __repr__(cls):
        return "<wrapped class '%s.%s'>" % (cls.__module__, cls.__name__)

    @classmethod
    def make_wrapper(mcls, name, attr_names):

        def __new__(mcls, nt, bases=None, attrs=None, **kw):
            return super(mcls, mcls).__new__(mcls, nt, bases, attrs)

        def __init__(mcls, to_wrap, **kw):
            for name in attr_names:
                try:
                    val = kw.pop(name)
                except KeyError:
                    msg = '%s expected keyword argument %r'
                    raise TypeError(msg % (mcls.__name__, name))
                setattr(mcls, name, val)
            if kw:
                raise TypeError('%s got unexpected keyword arguments: %r'
                                % kw.keys())
        wrapper = mcls(name, (mcls,), {'__new__': __new__,
                                       '__init__': __init__})
        return wrapper


def wrap_type(orig_type, **kw):
    tw_cls = orig_type
    if type(tw_cls) is not TypeWrapper:
        name = orig_type.__name__
        tw_cls = TypeWrapper(name, (tw_cls,), {})

    for k, v in kw.items():
        setattr(tw_cls, k, v)
    return tw_cls


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
