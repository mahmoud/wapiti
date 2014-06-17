import zlib
from hematite.compat import OrderedMultiDict as OMD
from hematite.compat.dictutils import PREV, NEXT, KEY, VALUE, _MISSING

ORIG_KEY = VALUE + 1


class Headers(OMD):
    """
    Headers is an OrderedMultiDict, a mapping that preserves order and
    subsequent values for the same key, built for string keys that one
    may want to query case-insensitively, but otherwise
    case-preservingly.
    """

    def _insert(self, k, v, orig_key):
        root = self.root
        cells = self._map.setdefault(k, [])
        last = root[PREV]
        cell = [last, root, k, v, orig_key]
        last[NEXT] = root[PREV] = cell
        cells.append(cell)

    def add(self, k, v, multi=False):
        self_insert = self._insert
        orig_key, k = k, k.lower()
        values = super(OMD, self).setdefault(k, [])
        if multi:
            for subv in v:
                self_insert(k, subv, orig_key)
            values.extend(v)
        else:
            self_insert(k, v, orig_key)
            values.append(v)

    def getlist(self, k):
        return super(Headers, self).getlist(k.lower())

    def get(self, k, default=None, multi=False):
        return super(Headers, self).get(k.lower(), default, multi)

    def setdefault(self, k, default=None):
        return super(Headers, self).setdefault(k.lower(), default)

    def copy(self):
        return self.__class__(self.iteritems(multi=True, preserve_case=True))

    def update(self, E=(), **F):
        if E is self:
            return

        self_add = self.add
        if isinstance(E, Headers):
            for k in E:
                if k in self:
                    del self[k]
            for k, v in E.iteritems(multi=True, preserve_case=True):
                self_add(k, v)
        elif isinstance(E, OMD):
            return super(Headers, self).update(E)
        elif hasattr(E, 'keys'):
            for k in E.keys():
                self[k] = E[k]
        else:
            seen = set()
            seen_add = seen.add
            for k, v in E:
                lower_k = k.lower()
                if lower_k not in seen and lower_k in self:
                    del self[k]
                    seen_add(lower_k)
                self_add(k, v)
        for k in F:
            self[k] = F[k]
        return

    def __getitem__(self, key):
        return super(Headers, self).__getitem__(key.lower())

    def get_cased_items(self, k):
        k = k.lower()
        return [(cell[ORIG_KEY], cell[VALUE]) for cell in self._map[k]]

    def __setitem__(self, k, v):
        orig_key, k = k, k.lower()
        if super(Headers, self).__contains__(k):
            self._remove_all(k)
        self._insert(k, v, orig_key)
        super(OMD, self).__setitem__(k, [v])

    def iteritems(self, multi=False, preserve_case=True):
        root = self.root
        curr = root[NEXT]
        if multi:
            key_idx = ORIG_KEY if preserve_case else KEY
            while curr is not root:
                yield curr[key_idx], curr[VALUE]
                curr = curr[NEXT]
        else:
            # this isn't so good
            items = super(Headers, self).iteritems(multi=False)
            if preserve_case:
                for key, value in items:
                    orig_key = self._map.get(key)[-1][ORIG_KEY]
                    yield orig_key, value
            else:
                for key, value in items:
                    yield key, value

    def itercaseditems(self):
        root = self.root
        curr = root[NEXT]
        while curr is not root:
            yield curr[ORIG_KEY], curr[KEY], curr[VALUE]
            curr = curr[NEXT]

    def popall(self, k, default=_MISSING):
        return super(Headers, self).popall(k.lower(), default)

    def poplast(self, k=_MISSING, default=_MISSING):
        k = k.lower() if k is not _MISSING else k
        return super(Headers, self).poplast(k)

    def items(self, multi=False, preserve_case=True):
        return list(self.iteritems(multi=multi,
                                   preserve_case=preserve_case))

    def __contains__(self, k):
        return super(Headers, self).__contains__(k.lower())


class Decompress(object):
    WBITS = {'gzip': (16 + zlib.MAX_WBITS,),
             'deflate': ()}

    def __init__(self, decompression):
        if decompression:
            try:
                args = self.WBITS[decompression]
            except KeyError:
                raise RuntimeError('unknown decompression '
                                   '{0}'.format(decompression))
            self.decompressor = zlib.decompressobj(*args)
            self.decompress = self.decompressor.decompress

    def decompress(self, data):
        return data


class ChunkedBody(Decompress):

    def __init__(self, chunks=None, decompression=None):
        super(ChunkedBody, self).__init__(decompression)
        self.chunks = chunks or []
        self.data = None
        self.nominal_length = None

    def send_chunk(self):
        return iter(self.chunks)

    def chunk_received(self, chunk):
        return self.chunks.append(self.decompress(chunk))

    def complete(self, length):
        self.data = ''.join(self.chunks)
        self.nominal_length = length

    def __repr__(self):
        cn = self.__class__.__name__
        if len(self.chunks) == 1:
            chunkstr = '1 chunk'
        else:
            chunkstr = '%s chunks' % len(self.chunks)
        compstr = 'complete' if self.data else 'incomplete'
        totsize = sum([len(c) for c in self.chunks])
        return '<%s %s, %s total bytes, %s>' % (cn, chunkstr, totsize, compstr)


class Body(Decompress):

    def __init__(self, body=None, decompression=None):
        super(Body, self).__init__(decompression)
        self.body = body or []
        self.data = None
        self.nominal_length = None

    def data_received(self, data):
        # To help determine Content-Length when Transfer-Encoding:
        # gzip
        return self.body.append(self.decompress(data))

    def send_data(self):
        return [self.body]

    def complete(self, length):
        self.data = ''.join(self.body)
        self.nominal_length = length

    def __repr__(self):
        cn = self.__class__.__name__
        partstr = ''
        if len(self.body) > 1:
            partstr = ' %s parts,' % len(self.body)
        compstr = 'complete' if self.data else 'incomplete'
        totsize = sum([len(p) for p in self.body])
        return '<%s%s %s total bytes, %s>' % (cn, partstr, totsize, compstr)


class UnifiedBody(object):
    def __init__(self):
        pass
