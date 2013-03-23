# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import WapitiException, DEFAULT_API_URL, OperationMeta
from models import PageIdentifier, CategoryInfo, RevisionInfo

import category
import feedback
import files
import links
import meta
import misc
import protection
import rand
import revisions
import templates
import user


for op in OperationMeta._all_ops:
    globals()[op.__name__] = op

ALL_OPERATIONS = tuple(OperationMeta._all_ops)
