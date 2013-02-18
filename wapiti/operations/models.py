# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime
from collections import namedtuple


def parse_timestamp(timestamp):
    return datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ')


class WikiException(Exception):
    pass


LanguageLink = namedtuple('LanguageLink', 'url language origin_page')
InterwikiLink = namedtuple('InterwikiLink', 'url prefix origin_page')
ExternalLink = namedtuple('ExternalLink', 'url origin_page')


class _PageIdentMixin(object):
    # this is just temporary so I can see what I'm doing a little better
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
            return super(_PageIdentMixin, self).__str__()

    def __str__(self):
        return self._to_string()

    def __repr__(self):
        try:
            return self._to_string(raise_exc=True)
        except:
            return super(_PageIdentMixin, self).__repr__()

    @property
    def page_id(self):
        return self.page_ident.page_id

    @property
    def ns(self):
        return self.page_ident.ns

    @property
    def title(self):
        return self.page_ident.title

    @property
    def source(self):
        return self.page_ident.source


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


class PageIdentifier(_PageIdentMixin):
    # lolololol masking mixin properties
    title, req_title, page_id, ns, source = (None,) * 5

    def __init__(self, title, page_id, ns, source,
                 req_title=None, subject_id=None, talk_id=None):
        self.title = title
        self.page_id = page_id
        self.ns = ns
        self.req_title = req_title or title
        self.source = source

        if self.is_subject_page:
            self.subject_id = page_id
            self.talk_id = talk_id
        elif self.is_talk_page:
            self.subject_id = subject_id
            self.talk_id = page_id
        else:
            raise ValueError('special or nonexistent namespace: %r' % ns)

    @property
    def is_subject_page(self):
        return (self.ns >= 0 and self.ns % 2 == 0)

    @property
    def is_talk_page(self):
        return (self.ns >= 0 and self.ns % 2 == 1)

    def get_subject_identifier(self):
        if self.is_subject_page:
            return self
        if self.subject_id is None:
            raise ValueError('subject_id not set')
        subj_title = title_talk2subject(self.title)
        subj_ns = self.ns - 1
        ret = PageIdentifier(subj_title,
                             self.subject_id,
                             subj_ns,
                             self.source,
                             self.req_title,
                             self.subject_id,
                             self.talk_id)
        return ret

    def get_talk_identifier(self):
        if self.is_talk_page:
            return self
        if self.talk_id is None:
            raise ValueError('talk_id not set')
        talk_title = title_subject2talk(self.title)
        talk_ns = self.ns + 1
        ret = PageIdentifier(talk_title,
                             self.talk_id,
                             talk_ns,
                             self.source,
                             self.req_title,
                             self.subject_id,
                             self.talk_id)
        return ret

    @classmethod
    def from_query(cls, res_dict, source, req_title=None):
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
                   parent_rev_id=rev['parentid'],
                   user_text=rev.get('user', '!userhidden'),
                   user_id=rev.get('userid', -1),
                   size=rev['size'],
                   timestamp=parse_timestamp(rev['timestamp']),
                   sha1=rev['sha1'],
                   comment=rev.get('comment', ''),
                   tags=rev['tags'],
                   text=rev.get('*'),
                   is_parsed=is_parsed)


class Revision(RevisionInfo):
    pass


class CategoryInfo(_PageIdentMixin):
    def __init__(self, page_ident, total_count, page_count, file_count,
                 subcat_count):
        self.page_ident = page_ident
        self.total_count = total_count
        self.page_count = page_count
        self.file_count = file_count
        self.subcat_count = subcat_count

    @property
    def page_id(self):
        return self.page_ident.page_id

    @property
    def ns(self):
        return self.page_ident.ns

    @property
    def title(self):
        return self.page_ident.title

    @property
    def source(self):
        return self.page_ident.source

    @classmethod
    def from_query(cls, res_dict, source):
        page_ident = PageIdentifier.from_query(res_dict, source)
        ci = res_dict.get('categoryinfo')
        if ci:
            size = ci['size']
            pages = ci['pages']
            files = ci['files']
            subcats = ci['subcats']
        else:
            size, pages, files, subcats = (0, 0, 0, 0)
        return cls(page_ident, size, pages, files, subcats)


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
