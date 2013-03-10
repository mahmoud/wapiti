# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import WapitiException, DEFAULT_API_URL
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
                      GetCategoryPagesRecursive,
                      GetAllCategoryInfos)
from links import (GetBacklinks,
                   GetLanguageLinks,
                   GetInterwikiLinks,
                   GetImages,
                   GetLinks,
                   GetExternalLinks)
from feedback import GetFeedbackV4, GetFeedbackV5
from revisions import (GetRevisionInfos,
                       GetCurrentContent,
                       GetCurrentTalkContent,
                       GetPageRevisionInfos)
from misc import (GetCoordinates,
                  GeoSearch,
                  GetImageInfos,
                  GetTemplates,
                  GetQueryPage,
                  GetRecentChanges,
                  GetAllImageInfos)
from meta import GetSourceInfo
from user import (GetUserContribs,
                  GetUserContribRevisions)
from templates import GetTranscludes, GetAllTranscludes

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
                  GetImageInfos,
                  GetCoordinates,
                  GeoSearch,
                  GetSourceInfo,
                  GetAllCategoryInfos,
                  GetAllImageInfos,
                  GetQueryPage,
                  GetRecentChanges,
                  GetTranscludes,
                  GetAllTranscludes,
                  GetPageRevisionInfos,
                  GetLinks,
                  GetExternalLinks,
                  GetUserContribs,
                  GetUserContribRevisions]
