# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime
from collections import namedtuple


def parse_timestamp(timestamp):
    return datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ')


LanguageLink = namedtuple('LanguageLink', 'url language origin_page')
InterwikiLink = namedtuple('InterwikiLink', 'url prefix origin_page')
ExternalLink = namedtuple('ExternalLink', 'url origin_page')

NamespaceDescriptor = namedtuple('NamespaceDescriptor', 'id title canonical')
InterwikiDescriptor = namedtuple('InterwikiDescriptor', 'alias url language')

WapitiModelAttr = namedtuple('WapitiModelAttr', 'name qd_key default display')


def title_talk2subject(title):
    talk_pref, _, title_suf = title.partition(':')
    subj_pref, _, _ = talk_pref.rpartition('talk')
    subj_pref = subj_pref.strip()
    new_title = subj_pref + ':' + title_suf
    new_title = new_title.lstrip(':')
    return new_title


def title_subject2talk(title):
    subj_pref, _, title_suf = title.partition(':')
    subj_pref = subj_pref.strip()
    if not subj_pref:
        talk_pref = 'Talk'
    elif subj_pref.endswith('talk'):
        talk_pref = subj_pref
    else:
        talk_pref = subj_pref + ' talk'
    new_title = talk_pref + ':' + title_suf
    return new_title


class WapitiModelMeta(type):
    attributes = {}
    defaults = {}

    def __new__(cls, name, bases, attrs):
        all_attributes = {}
        all_defaults = {}
        for base in bases:
            all_attributes.update(getattr(base, 'attributes', {}))
            all_defaults.update(getattr(base, 'defaults', {}))
        all_attributes.update(attrs.get('attributes', {}))
        all_defaults.update(attrs.get('defaults', {}))
        attrs['attributes'] = all_attributes
        attrs['defaults'] = all_defaults
        ret = super(WapitiModelMeta, cls).__new__(cls, name, bases, attrs)
        return ret


class WapitiModelBase(object):

    __metaclass__ = WapitiModelMeta
    attributes = {}
    defaults = {}

    def __init__(self, **kw):
        missing = []
        for m_attr_name in self.attributes:
            try:
                val = kw.pop(m_attr_name)
            except KeyError:
                try:
                    val = self.defaults[m_attr_name]
                except KeyError:
                    missing.append(m_attr_name)
                    continue
            setattr(self, m_attr_name, val)
        if missing:
            raise ValueError('missing expected keyword arguments: %r'
                             % missing)
        # TODO: raise on unexpected keyword arguments?
        return

    @classmethod
    def from_query(cls, q_dict, **kw):
        kwargs = {}
        all_q_dict = dict(kw)
        all_q_dict.update(q_dict)
        for m_attr_name, q_dict_key in cls.attributes.items():
            if q_dict_key is None:
                continue
            try:
                kwargs[m_attr_name] = all_q_dict[q_dict_key]
            except KeyError:
                pass
        return cls(**kwargs)


class PageIdentifier(WapitiModelBase):
    attributes = {'title': 'title',
                  'page_id': 'pageid',
                  'ns': 'ns',
                  'source': 'source'}
    defaults = {}

    @property
    def is_subject_page(self):
        return (self.ns >= 0 and self.ns % 2 == 0)

    @property
    def is_talk_page(self):
        return (self.ns >= 0 and self.ns % 2 == 1)

    def _to_string(self, raise_exc=False):
        try:
            class_name = self.__class__.__name__
            return (u'%s(%r, %r, %r, %r)'
                    % (class_name,
                       self.title,
                       self.page_id,
                       self.ns,
                       self.source))
        except AttributeError:
            if raise_exc:
                raise
            return super(PageIdentifier, self).__str__()

    def __str__(self):
        return self._to_string()

    def __repr__(self):
        try:
            return self._to_string(raise_exc=True)
        except:
            return super(PageIdentifier, self).__repr__()


class PageInfo(PageIdentifier):
    attributes = {'subject_id': 'subjectid',
                  'talk_id': 'talkid'}
    defaults = {'subject_id': None,
                'talk_id': None}

    def __init__(self, **kw):
        req_title = kw.pop('req_title', None)
        super(PageInfo, self).__init__(**kw)
        self.req_title = req_title or self.title

        if self.is_subject_page:
            self.subject_id = self.page_id
        elif self.is_talk_page:
            self.talk_id = self.page_id
        else:
            raise ValueError('special or nonexistent namespace: %r' % self.ns)

    def get_subject_info(self):
        if self.is_subject_page:
            return self
        if self.subject_id is None:
            raise ValueError('subject_id not set')
        subj_title = title_talk2subject(self.title)
        subj_ns = self.ns - 1
        kwargs = dict(self.__dict__)
        kwargs['title'] = subj_title
        kwargs['ns'] = subj_ns
        return PageInfo(**kwargs)

    def get_talk_info(self):
        if self.is_talk_page:
            return self
        if self.talk_id is None:
            raise ValueError('talk_id not set')
        talk_title = title_subject2talk(self.title)
        talk_ns = self.ns + 1
<<<<<<< HEAD
        kwargs = dict(self.__dict__)
        kwargs['title'] = talk_title
        kwargs['ns'] = talk_ns
        return PageInfo(**kwargs)


class CategoryInfo(PageInfo):
    attributes = {'total_count': 'size',
                  'page_count': 'pages',
                  'file_count': 'files',
                  'subcat_count': 'subcats'}
    defaults = {'total_count': 0,
                'page_count': 0,
                'file_count': 0,
                'subcat_count': 0}


class RevisionInfo(PageIdentifier):
    attributes = {'rev_id': 'revid',
                  'size': 'size',
                  'user_text': 'user',
                  'user_id': 'userid',
                  'timestamp': 'timestamp',
                  'comment': 'comment',
                  'parsed_comment': 'parsedcomment',
                  'tags': 'tags'}

    # note that certain revisions may have hidden the fields
    # user_id, user_text, and comment for administrative reasons,
    # aka "oversighting"
    # TODO: is oversighting better handled in operation?
    defaults = {'user_text': '!userhidden',
                'userid': -1,
                'comment': ''}

    def __init__(self, *a, **kw):
        super(RevisionInfo, self).__init__(*a, **kw)
        self.timestamp = parse_timestamp(self.timestamp)
=======
        ret = PageIdentifier(talk_title,
                             self.talk_id,
                             talk_ns,
                             self.source,
                             self.req_title,
                             self.subject_id,
                             self.talk_id)
        return ret

    @classmethod
    def from_query(cls, res_dict, input_source, req_title=None):
        try:
            title = res_dict['title']
            page_id = res_dict['pageid']
            ns = res_dict['ns']
            subject_id = res_dict.get('subjectid')
            talk_id = res_dict.get('talkid')
        except KeyError:
            if callable(getattr(res_dict, 'keys', None)):
                disp = res_dict.keys()
            else:
                disp = repr(res_dict)
                if len(disp) > 30:
                    disp = disp[:30] + '...'
            raise ValueError('page identifier expected title,'
                             ' page_id, and namespace. received: "%s"'
                             % disp)
        try:
            source = input_source
        except ValueError:
            raise ValueError('please specify source')
        return cls(title, page_id, ns, source, req_title, subject_id, talk_id)


class RevisionInfo(_PageIdentMixin):
    def __init__(self, page_ident, rev_id, parent_rev_id, user_text,
                 user_id, size, timestamp, sha1, comment, tags,
                 text=None, is_parsed=None):
        self.page_ident = page_ident
        self.rev_id = rev_id,
        self.parent_rev_id = parent_rev_id
        self.user_text = user_text
        self.user_id = user_id
        self.size = size
        self.timestamp = timestamp
        self.sha1 = sha1
        self.comment = comment
        self.tags = tags
        self.text = text or ''
        self.is_parsed = is_parsed

    @classmethod
    def from_query(cls, page_ident, res_dict, source, is_parsed=None):
        # note that certain revisions may have hidden the fields
        # user_id, user_text, and comment for administrative reasons,
        # aka "oversighting"
        rev = res_dict
        return cls(page_ident=page_ident,
                   rev_id=rev['revid'],
                   parent_rev_id=rev.get('parentid'),
                   user_text=rev.get('user', '!userhidden'),
                   user_id=rev.get('userid', -1),
                   size=rev.get('size'),
                   timestamp=parse_timestamp(rev['timestamp']),
                   sha1=rev.get('sha1'),
                   comment=rev.get('comment', ''),
                   tags=rev['tags'],
                   text=rev.get('*'),
                   is_parsed=is_parsed)
>>>>>>> 2fdfcd687d903d72d75698eb72225bf4935c8c05


class Revision(RevisionInfo):
    attributes = {'parent_rev_id': 'parentid',
                  'content': '*',
                  'is_parsed': 'is_parsed'}
    defaults = {'content': ''}  # necessary?


#
# Protections
#
NEW = 'NEW'
AUTOCONFIRMED = 'AUTOCONFIRMED'
SYSOP = 'SYSOP'
PROTECTION_ACTIONS = ('create', 'edit', 'move', 'upload')


Protection = namedtuple('Protection', 'level, expiry')


class ProtectionInfo(object):
    # TODO: turn into mixin, add to PageIdentifier
    """
    For more info on protection,
    see https://en.wikipedia.org/wiki/Wikipedia:Protection_policy
    """
    levels = {
        'new': NEW,
        'autoconfirmed': AUTOCONFIRMED,
        'sysop': SYSOP,
    }

    def __init__(self, protections, page_ident=None):
        self.page_ident = page_ident

        protections = protections or {}
        self.protections = {}
        for p in protections:
            if not p['expiry'] == 'infinity':
                expiry = parse_timestamp(p['expiry'])
            else:
                expiry = 'infinity'
            level = self.levels[p['level']]
            self.protections[p['type']] = Protection(level, expiry)

    @property
    def has_protection(self):
        return any([x.level != NEW for x in self.protections.values()])

    @property
    def has_indef(self):
        return any([x.expiry == 'infinity' for x in self.protections.values()])

    @property
    def is_full_prot(self):
        try:
            if self.protections['edit'].level == SYSOP and \
                    self.protections['move'].level == SYSOP:
                return True
            else:
                return False
        except (KeyError, AttributeError):
            return False

    @property
    def is_semi_prot(self):
        try:
            if self.protections['edit'].level == AUTOCONFIRMED:
                return True
            else:
                return False
        except (KeyError, AttributeError):
            return False

    def __repr__(self):
        return u'ProtectionInfo(%r)' % self.protections


class CoordinateIndentifier(object):
    def __init__(self, coord, page_ident=None):
        self.page_ident = page_ident
        self.lat = coord.get('lat')
        self.lon = coord.get('lon')
        self.type = coord.get('type')
        self.name = coord.get('name')
        self.dim = coord.get('dim')
        self.country = coord.get('country')
        self.region = coord.get('region')
        if coord.get('primary', False):
            self.primary = True
        else:
            self.primary = False
        return
