# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import WapitiException, DEFAULT_API_URL, OperationMeta
from models import PageIdentifier, CategoryInfo, RevisionInfo

import rand
import revisions
import category
import templates
import user
import protection
import misc
import files
import feedback

for op in OperationMeta._all_ops:
    globals()[op.__name__] = op

ALL_OPERATIONS = tuple(OperationMeta._all_ops)
