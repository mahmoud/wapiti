# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import WapitiException
from models import PageIdentifier, CategoryInfo, RevisionInfo

from rand import GetRandom
from templates import GetTranscludes
from protection import GetProtections
from category import (GetCategoryList,
                      GetCategory,
                      GetCategoryPages,
                      GetSubcategoryInfos,
                      GetFlattenedCategory,
                      GetCategoryRecursive,
                      GetCategoryPagesRecursive)
from links import (GetBacklinks, 
                   GetLanguageLinks, 
                   GetInterwikiLinks,
                   GetImages)
from feedback import GetFeedbackV4, GetFeedbackV5
from revisions import (GetRevisionInfos,
                       GetCurrentContent,
                       GetCurrentTalkContent)
from misc import GetCoordinates, GeoSearch

ALL_OPERATIONS = [GetRandom,
                  GetTranscludes,
                  GetProtections,
                  GetCategoryList,
                  GetCategory,
                  GetCategoryPages,
                  GetSubcategoryInfos,
                  GetFlattenedCategory,
                  GetCategoryRecursive,
                  GetCategoryPagesRecursive,
                  GetBacklinks,
                  GetLanguageLinks,
                  GetInterwikiLinks,
                  GetFeedbackV4,
                  GetFeedbackV5,
                  GetRevisionInfos,
                  GetCurrentContent,
                  GetCurrentTalkContent,
                  GetImages,
                  GetCoordinates,
                  GeoSearch]
