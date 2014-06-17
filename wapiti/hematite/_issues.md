# Issues discovered with other implementations

## Werkzeug

* When Werkzeug detects an item is quoted, it prematurely unquotes it,
  leaving internal escaping in place. See parse_dict_header for
  example.
* ETags are also not internally unquoted. If quoted, quotes are just
  pulled off the ends, leaving internal escaping in place.
* Werkzeug raises an exception if an ETag has a quote in it, even
  though it's technically a quoted-string in RFC2616
* Chokes on non-canonical (but legal) range specs like:
  bytes=500-700,601-999

## Requests

* Don't even get me started.
