# -*- coding: utf-8 -*-

from heapq import heappush, heappop
import itertools


def is_scalar(obj):
    return not hasattr(obj, '__iter__') or isinstance(obj, basestring)


def prefixed(arg, prefix=None):
    if prefix and not arg.startswith(prefix):
        arg = prefix + arg
    return arg


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
