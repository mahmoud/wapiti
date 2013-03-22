# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import QueryOperation
from params import MultiParam, StaticParam
from models import PageInfo, ImageInfo
from utils import OperationExample


DEFAULT_IMAGE_PROPS = ['timestamp', 'user', 'userid', 'comment', 'parsedcomment',
                       'url', 'size', 'dimensions', 'sha1', 'mime', 'mediatype',
                       'metadata', 'bitdepth']
IMAGE_INFO_PROPS = DEFAULT_IMAGE_PROPS + ['thumbmime', 'archivename']


class GetImages(QueryOperation):
    """
    Fetch the images embedded on pages.
    """
    field_prefix = 'gim'
    input_field = MultiParam('titles', key_prefix=False)
    fields = [StaticParam('generator', 'images'),
              StaticParam('prop', 'info'),
              StaticParam('inprop', 'subjectid|talkid|protection')]
    output_type = [PageInfo]
    examples = [OperationExample('Coffee')]

    def extract_results(self, query_resp):
        ret = []
        for pid, pid_dict in query_resp['pages'].iteritems():
            if pid.startswith('-'):
                pid_dict['pageid'] = None  # TODO: breaks consistency :/
            try:
                page_ident = PageInfo.from_query(pid_dict,
                                                 source=self.source)
            except ValueError:
                continue
            ret.append(page_ident)
        return ret


class GetImageInfos(QueryOperation):
    field_prefix = 'ii'
    input_field = MultiParam('titles', key_prefix=False)
    fields = [StaticParam('prop', 'imageinfo'),
              StaticParam('iiprop', IMAGE_INFO_PROPS)]
    output_type = [ImageInfo]

    def extract_results(self, query_resp):
        ret = []
        for k, pid_dict in query_resp['pages'].iteritems():
            if int(k) < 0 and pid_dict['imagerepository'] != 'local':
                pid_dict['pageid'] = 'shared'
                pid_dict['revid'] = 'shared'
            try:
                pid_dict.update(pid_dict.get('imageinfo', [{}])[0])
                image_info = ImageInfo.from_query(pid_dict,
                                                  source=self.source)
            except ValueError as e:
                print e
                continue
            ret.append(image_info)
        return ret


class GetAllImageInfos(GetImageInfos):
    field_prefix = 'gai'
    input_field = None
    fields = [StaticParam('generator', 'allimages'),
              StaticParam('prop', 'imageinfo'),
              StaticParam('gaiprop', DEFAULT_IMAGE_PROPS)]
    examples = [OperationExample()]
