# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import Sequence, Set
from utils import is_scalar, prefixed


def param_list2str(p_list, prefix=None, keep_empty=False):
    if is_scalar(p_list):
        p_list = param_str2list(p_list, keep_empty)
    u_p_list = [unicode(p) for p in p_list]
    ret = "|".join([prefixed(t, prefix)
                    for t in u_p_list if (t or keep_empty)])
    return unicode(ret)


def param_str2list(p, keep_empty=False):
    p = p or ''
    if is_scalar(p):
        p = unicode(p)
    else:
        p = param_list2str(p)
    p_list = p.split('|')
    if not keep_empty:
        p_list = [sp for sp in p_list if sp]
    return p_list


def normalize_param(p, prefix=None, multi=None):
    p_list = param_str2list(p)
    if multi is False:
        if len(p_list) > 1:
            tmpl = 'expected singular query parameter, not %r'
            raise ValueError(tmpl % p)
    return param_list2str(p_list, prefix)


class Param(object):
    def __init__(self, key, default=None, val_prefix=None, **kw):
        if not key:
            raise ValueError('expected key, not %r' % key)
        self.key = unicode(key)
        self.val_prefix = val_prefix
        param_attr = kw.pop('attr', None)
        coerce_func = kw.pop('coerce', None)
        if coerce_func is None:
            if isinstance(param_attr, basestring):
                coerce_func = lambda x: getattr(x, param_attr)
            elif param_attr is None:
                coerce_func = lambda x: x
            else:
                raise TypeError("'attr' expected string")
        elif not callable(coerce_func):
            raise TypeError("'coerce' expected callable")
        self.coerce_func = coerce_func
        self.accept_str = kw.pop('accept_str', True)
        self.key_prefix = kw.pop('key_prefix', True)  # True = filled in later
        self.required = kw.pop('required', False)
        self.multi = kw.pop('multi', None)
        if kw:
            raise ValueError('unexpected keyword argument(s): %r' % kw)
        if default is not None:
            default = normalize_param(default, self.val_prefix, self.multi)
        self.default = default

    def get_key(self, key_prefix=None):
        if self.key_prefix:
            prefix = key_prefix
            if prefix is None:
                prefix = self.key_prefix
            if isinstance(prefix, basestring):
                prefix = unicode(prefix)
            else:
                raise TypeError('expected valid string prefix')
        else:
            prefix = ''
        return prefix + self.key

    def _coerce_value(self, value):
        # TODO: it's real late and this is a bit of a sty
        # also, in some cases the bar-split normalization
        # should not occur (e.g., on a URL)
        if not value or isinstance(value, basestring):
            return value
        if isinstance(value, (Sequence, Set)):
            coerced = []
            for v in value:
                if isinstance(v, basestring):
                    coerced.append(v)
                else:
                    coerced.append(self.coerce_func(v))
        else:
            coerced = self.coerce_func(v)
        return coerced

    def get_value(self, value, prefix=None):
        if prefix is None:
            prefix = self.val_prefix
        value = self._coerce_value(value)
        norm_val = normalize_param(value, prefix, self.multi)
        val = norm_val or self.default
        if val is None and self.required:
            raise ValueError('%r param is required' % self.key)
        return val

    def get_value_list(self, value, prefix=None):
        return param_str2list(self.get_value(value, prefix))

    def get_tuple(self):
        return (self.key, self.value)

    def get_tuple_from_kwargs(self, **kwargs):
        """
        Picks up appropriate values from kwargs,
        returns the defaults if nothing matches.
        """
        pass

    __call__ = get_value


class SingleParam(Param):
    def __init__(self, *a, **kw):
        kw['multi'] = False
        super(SingleParam, self).__init__(*a, **kw)


class MultiParam(Param):
    def __init__(self, *a, **kw):
        kw['multi'] = True
        super(MultiParam, self).__init__(*a, **kw)


class StaticParam(Param):
    def __init__(self, key, value):
        super(StaticParam, self).__init__(key, value)

    def get_key(self, *a, **kw):
        return self.key

    def get_value(self, *a, **kw):
        return self.default
