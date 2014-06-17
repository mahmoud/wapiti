from abc import ABCMeta
from collections import namedtuple


class Message(object):
    __metaclass__ = ABCMeta


def make_message(name, *fields):
    _msg = namedtuple(name, ('type',) + fields)

    def __new__(_cls, *args, **kwargs):
        # can't use super because the class hasn't been defined yet
        # :(
        return _msg.__new__(_cls, _cls.type, *args, **kwargs)

    msg = type(name, (_msg,), {'__new__': __new__,
                               'type': name.lower()})
    Message.register(msg)
    return msg

HaveData = make_message('HaveData', 'value')
HaveLine = make_message('HaveLine', 'value')
HavePeek = make_message('HavePeek', 'value')

NeedData = make_message('NeedData', 'amount')
NeedLine = make_message('NeedLine', 'none')(None)
NeedPeek = make_message('NeedPeek', 'amount')

Empty = make_message('Empty', 'none')(None)
Complete = make_message('Complete', 'none')(None)
WantDisconnect = make_message('WantDisconnect', 'none')(None)
