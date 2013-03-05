# -*- coding: utf-8 -*-

from heapq import heappush, heappop
import itertools


def is_scalar(obj):
    return not hasattr(obj, '__iter__') or isinstance(obj, basestring)


def prefixed(arg, prefix=None):
    if prefix and not arg.startswith(prefix):
        arg = prefix + arg
    return arg


class TypeWrapperMeta(type):
    def __new__(mcls, name, bases, attrs):
        twm_bases = [b for b in bases if isinstance(b, TypeWrapperMeta)]
        if twm_bases:
            raise TypeError('%s attempted to subclass a wrapped type: %r'
                            % (name, twm_bases))

        ret = super(TypeWrapperMeta, mcls).__new__(mcls, name, bases, attrs)
        ret._wrapped_attrs = set()
        return ret

    def __setattr__(cls, name, val):
        super(TypeWrapperMeta, cls).__setattr__(name, val)
        if not name == '_wrapped_attrs':
            cls._wrapped_attrs.add(name)

    def __delattr__(cls, name, val):
        super(TypeWrapperMeta, cls).__delattr__(name, val)
        try:
            cls._wrapped_attrs.remove(name)
        except KeyError:
            pass


def wrap_type(orig_type, **kw):
    tw_cls = orig_type
    if not isinstance(tw_cls, TypeWrapperMeta):
        name = orig_type.__name__
        tw_cls = TypeWrapperMeta(name, (tw_cls,), {})

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
