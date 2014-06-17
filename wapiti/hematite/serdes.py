# -*- coding: utf-8 -*-

import re
import time
from datetime import datetime, timedelta

from hematite.constants import HEADER_CASE_MAP
from hematite.raw import core
from hematite.raw.datastructures import Headers


# these two functions are shared by Request and Response. Could use a
# metaclass maybe, but we'll see.

def _init_headers(self):
    self.headers = Headers()
    # plenty of ways to arrange this
    hf_map = self._header_field_map
    for hname, lower_hname, hval in self._raw_headers.itercaseditems():
        try:
            norm_hname = HEADER_CASE_MAP[lower_hname]
            field = hf_map[norm_hname]
        except KeyError:
            # preserves insertion order and duplicates
            self.headers.add(hname, default_header_from_bytes(hval))
        else:
            if field.is_foldable:
                if norm_hname in self.headers:
                    continue
                # TODO: this won't catch e.g., Cache-Control + CACHE-CONTROL
                # in the same preamble/envelope
                val_list = self._raw_headers.getlist(hname)
                hval = ','.join(val_list)
            field.__set__(self, hval)


def _get_headers(self, drop_empty=True):
    # TODO: option for unserialized?
    ret = Headers()
    hf_map = self._header_field_map
    for hname, hval in self.headers.items(multi=True):
        if drop_empty and hval is None or hval == '':
            # TODO: gonna need a field.is_empty or something
            continue
        try:
            field = hf_map[hname]
        except KeyError:
            ret.add(hname, default_header_to_bytes(hval))
        else:
            ret.add(hname, field.to_bytes(hval))
    return ret

###


def quote_header_value(value, quote_token=False):
    value = str(value)          # TODO: encoding arg!
    if not value or (not quote_token and core.TOKEN.match(value)):
        return value
    return '"%s"' % value.replace('\\', '\\\\').replace('"', '\\"')


def unquote_header_value(value):
    # watch out for certain cases with filenames
    if value and value[0] == value[-1] == '"':
        value = value[1:-1]
        #if not is_filename or value[:2] != '\\\\':
        return value.replace('\\\\', '\\').replace('\\"', '"')
    return value


def default_header_from_bytes(bytestr):
    # TODO: safe to do unquoting once, pre-decode?
    try:
        return unquote_header_value(bytestr.decode('latin-1'))
    except:
        try:
            return unquote_header_value(bytestr)
        except:
            return bytestr


def default_header_to_bytes(val):
    return unicode(val).encode('latin-1')


def list_header_from_bytes(val, unquote=True):
    "e.g., Accept-Ranges. skips blank values, per the RFC."
    ret = []
    for v in _list_header_from_bytes(val):
        if not v:
            continue
        if unquote and v[0] == '"' == v[-1]:
            v = unquote_header_value(v)
        ret.append(v)
    return ret


def list_header_to_bytes(val):
    return ', '.join([quote_header_value(v) for v in val])


def items_header_from_bytes(val, unquote=True, sep=None):
    """
    TODO: I think unquote is always true here? values can always be
    quoted.
    """
    ret, sep = [], sep or ','
    for item in _list_header_from_bytes(val, sep=sep):
        key, _part, value = item.partition('=')
        if not _part:
            ret.append((key, None))
            continue
        if unquote and value and value[0] == '"' == value[-1]:
            value = unquote_header_value(value)
        ret.append((key, value))
    return ret


def items_header_to_bytes(items, sep=None):
    parts, sep = [], sep or ', '
    for key, val in items:
        if val is None or val == '':
            parts.append(key)
        else:
            parts.append('='.join([str(key), quote_header_value(val)]))
    return sep.join(parts)

_accept_re = re.compile(r'('
                        r'(?P<media_type>[^,;]+)'
                        r'(;\s*q='
                        r'(?P<quality>[^,;]+))?),?')


def accept_header_from_bytes(val):
    """
    Parses an Accept-style header (with q-vals) into a list of tuples
    of `(media_type, quality)`. Input order is maintained (does not sort
    by quality value).

    Does not check media_type format for mimetype-style format. Does
    not implement "accept-extension", as they seem to have never been
    used. (search for "text/html;level=1" in RFC2616 to see an example)

    >>> accept_header_from_bytes('audio/*; q=0.2 , audio/basic')
    [('audio/*', 0.2), ('audio/basic', 1.0)]
    """
    ret = []
    for match in _accept_re.finditer(val):
        media_type = (match.group('media_type') or '').strip()
        if not media_type:
            continue
        try:
            quality = max(min(float(match.group('quality') or 1.0), 1.0), 0.0)
        except:
            quality = 0.0
        ret.append((media_type, quality))
    return ret


def accept_header_to_bytes(val):
    parts = []
    for mediatype, qval in val:
        cur = mediatype
        if qval != 1.0:
            cur += ';q=' + str(qval)
        parts.append(cur)
    return ','.join(parts)


def content_header_from_bytes(val):
    """
    Parses a Content-Type header, a combination of list and key-value
    headers, separated by semicolons.. RFC2231 is crazy, so this initial
    implementation only supports features I've seen before.

    (Also used for the Content-Disposition header)

    # TODO: find examples for tests
    # TODO: implement some _crazy_ features:
    #  - rollup of asterisk-indexed parts (param continuations) (RFC2231 #3)
    #  - parameter encodings and languages (RFC2231 #4)
    """
    items = items_header_from_bytes(val, sep=';')
    if not items:
        return '', []
    media_type = items[0][0]
    return media_type, items[1:]


def http_date_from_bytes(date_str):
    # TODO: is the strip really necessary?
    timetuple = _date_tz_from_bytes(date_str.strip())
    tz_seconds = timetuple[-1] or 0
    tz_offset = timedelta(seconds=tz_seconds)
    return datetime(*timetuple[:7]) - tz_offset


_dayname = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
_monthname = [None,  # Dummy so we can use 1-based month numbers
              "Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def http_date_to_bytes(date_val=None, sep=' '):
    """
    Output an RFC1123-formatted date suitable for the Date header and
    cookies (with sep='-').

    # TODO: might have to revisit byte string handling
    """
    if date_val is None:
        time_tuple = time.gmtime()
    elif isinstance(date_val, datetime):
        time_tuple = date_val.utctimetuple()
    else:
        raise ValueError()  # support other timestamps?

    year, month, day, hh, mm, ss, wd, y, z = time_tuple
    return ("%s, %02d%s%3s%s%4d %02d:%02d:%02d GMT" %
            (_dayname[wd], day, sep, _monthname[month], sep, year, hh, mm, ss))


def range_spec_from_bytes(bytestr):
    # TODO: is bytes=500 valid? or does it have to be bytes=500-500
    unit, _, range_str = bytestr.partition('=')
    unit = unit.strip().lower()
    if not unit:
        return None
    last_end, range_list = 0, []

    for rng in range_str.split(','):
        rng = rng.strip()
        if '-' not in rng:
            raise ValueError('invalid byte range specifier: %r' % bytestr)
        if rng[:1] == '-':
            if last_end < 0:
                raise ValueError('invalid byte range specifier: %r' % bytestr)
            begin, end, last_end = int(rng), None, -1
        else:
            begin, _, end = rng.partition('-')
            begin = int(begin)
            if end:
                end = int(end)
                if begin > end:
                    raise ValueError('invalid byte range specifier: %r'
                                     % bytestr)
            else:
                end = None
            last_end = end
        range_list.append((begin, end))
    return (unit, range_list)


def range_spec_to_bytes(val):
    if not val:
        return ''
    unit, ranges = val
    ret = str(unit) + '='
    range_parts = []
    for begin, end in ranges:
        cur = str(begin)
        if begin >= 0:
            cur += '-'
        if end is not None:
            cur += str(end)
        range_parts.append(cur)
    ret += ','.join(range_parts)
    return ret


def content_range_spec_from_bytes(bytestr):
    stripped = bytestr.strip()
    if not stripped:
        return None
    try:
        unit, resp_range_spec = stripped.split(None, 1)
    except TypeError:
        raise ValueError('invalid content range spec: %r' % bytestr)
    resp_range, _, total_length = resp_range_spec.partition('/')
    try:
        total_length = int(total_length)
    except ValueError:
        if total_length == '*':
            pass  # TODO: total_length = None ?
        else:
            raise ValueError('invalid content range spec: %r (expected int'
                             ' or "*" for total_length)' % bytestr)
    begin, _, end = resp_range.partition('-')
    try:
        begin, end = int(begin), int(end)
    except ValueError:
        raise ValueError('invalid content range spec: %r (invalid range)'
                         % bytestr)
    return unit, begin, end, total_length


def content_range_spec_to_bytes(val):
    unit, begin, end, total_length = val
    parts = [unit, ' ']
    if begin is None:
        parts.append('*')
    else:
        parts.extend([str(begin), '-', str(end)])
    parts.extend(['/', str(total_length)])
    return ''.join(parts)


def retry_after_from_bytes(bytestr):
    try:
        seconds = int(bytestr)
        val = timedelta(seconds=seconds)
    except ValueError:
        try:
            val = http_date_from_bytes(bytestr)
        except:
            raise ValueError('expected HTTP-date or delta-seconds for'
                             ' Retry-After, not %r' % bytestr)
    return val


def retry_after_to_bytes(val):
    if isinstance(val, timedelta):
        return bytes(int(round(total_seconds(val))))
    else:
        return http_date_to_bytes(val)


def _list_header_from_bytes(bytestr, sep=None):
    """Parse lists as described by RFC 2068 Section 2.

    In particular, parse comma-separated lists where the elements of
    the list may include quoted-strings.  A quoted-string could
    contain a comma.  A non-quoted string could have quotes in the
    middle.  Neither commas nor quotes count if they are escaped.
    Only double-quotes count, not single-quotes.

    (based on urllib2 from the stdlib)
    """
    bytestr = bytestr.strip()
    res, part, sep = [], '', sep or ','

    escape = quote = False
    for cur in bytestr:
        if escape:
            part += cur
            escape = False
            continue
        if quote:
            if cur == '\\':
                escape = True
                continue
            elif cur == '"':
                quote = False
            part += cur
            continue

        if cur == sep:
            res.append(part)
            part = ''
            continue

        if cur == '"':
            quote = True

        part += cur

    # append last part
    if part:
        res.append(part)

    return [part.strip() for part in res]


def _date_tz_from_bytes(data):
    """Convert a date string to a time tuple.

    Accounts for military timezones (for some reason).

    # TODO: raise exceptions instead of returning None
    # TODO: non-GMT named timezone support necessary?

    Based on the built-in email package from Python 2.7.
    """
    data = data.split()
    # The FWS after the comma after the day-of-week is optional, so search and
    # adjust for this.
    if data[0].endswith(',') or data[0].lower() in _daynames:
        # There's a dayname here. Skip it
        del data[0]
    else:
        i = data[0].rfind(',')
        if i >= 0:
            data[0] = data[0][i+1:]
    if len(data) == 3:  # RFC 850 date, deprecated
        stuff = data[0].split('-')
        if len(stuff) == 3:
            data = stuff + data[1:]
    if len(data) == 4:
        s = data[3]
        i = s.find('+')
        if i > 0:
            data[3:] = [s[:i], s[i+1:]]
        else:
            data.append('')  # Dummy tz
    if len(data) < 5:
        return None
    data = data[:5]
    dd, mm, yy, tm, tz = data
    mm = mm.lower()
    if mm not in _monthnames:
        dd, mm = mm, dd.lower()
        if mm not in _monthnames:
            return None
    mm = _monthnames.index(mm) + 1
    if mm > 12:
        mm -= 12
    if dd[-1] == ',':
        dd = dd[:-1]
    i = yy.find(':')
    if i > 0:
        yy, tm = tm, yy
    if yy[-1] == ',':
        yy = yy[:-1]
    if not yy[0].isdigit():
        yy, tz = tz, yy
    if tm[-1] == ',':
        tm = tm[:-1]
    tm = tm.split(':')
    if len(tm) == 2:
        [thh, tmm] = tm
        tss = '0'
    elif len(tm) == 3:
        [thh, tmm, tss] = tm
    else:
        return None
    try:
        yy, dd, thh, tmm, tss = int(yy), int(dd), int(thh), int(tmm), int(tss)
    except ValueError:
        return None
    # Check for a yy specified in two-digit format, then convert it to the
    # appropriate four-digit format, according to the POSIX standard. RFC 822
    # calls for a two-digit yy, but RFC 2822 (which obsoletes RFC 822)
    # mandates a 4-digit yy. For more information, see the documentation for
    # the time module.
    if yy < 100:
        # The year is between 1969 and 1999 (inclusive).
        if yy > 68:
            yy += 1900
        # The year is between 2000 and 2068 (inclusive).
        else:
            yy += 2000
    tzoffset = None
    tz = tz.upper()
    if tz in _timezones:
        tzoffset = _timezones[tz]
    else:
        try:
            tzoffset = int(tz)
        except ValueError:
            pass
    # Convert a timezone offset into seconds ; -0500 -> -18000
    if tzoffset:
        if tzoffset < 0:
            tzsign = -1
            tzoffset = -tzoffset
        else:
            tzsign = 1
        tzoffset = tzsign * ((tzoffset // 100) * 3600 + (tzoffset % 100) * 60)
    # Daylight Saving Time flag is set to -1, since DST is unknown.
    return yy, mm, dd, thh, tmm, tss, 0, 1, -1, tzoffset


_monthnames = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul',
               'aug', 'sep', 'oct', 'nov', 'dec',
               'january', 'february', 'march', 'april', 'may', 'june', 'july',
               'august', 'september', 'october', 'november', 'december']

_daynames = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']

# The timezone table does not include the military time zones defined
# in RFC822, other than Z.  According to RFC1123, the description in
# RFC822 gets the signs wrong, so we can't rely on any such time
# zones.  RFC1123 recommends that numeric timezone indicators be used
# instead of timezone names.

_timezones = {'UT':0, 'UTC':0, 'GMT':0, 'Z':0,
              'AST': -400, 'ADT': -300,  # Atlantic (used in Canada)
              'EST': -500, 'EDT': -400,  # Eastern
              'CST': -600, 'CDT': -500,  # Central
              'MST': -700, 'MDT': -600,  # Mountain
              'PST': -800, 'PDT': -700   # Pacific
              }


def total_seconds(td):
    """\
    A pure-Python implementation of Python 2.7's timedelta.total_seconds().

    Accepts a timedelta object, returns number of total seconds.

    >>> from datetime import timedelta
    >>> td = timedelta(days=4, seconds=33)
    >>> total_seconds(td)
    345633.0

    (from boltons)
    """
    a_milli = 1000000.0
    td_ds = td.seconds + (td.days * 86400)  # 24 * 60 * 60
    td_micro = td.microseconds + (td_ds * a_milli)
    return td_micro / a_milli
