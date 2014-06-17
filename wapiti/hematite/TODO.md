# TODO

## Refactors

- Get off of namedtuple as base class for parser components?

## Issues

- coverage/pytest-cov not seeing globals as covered (e.g., function
  defs or global regexes)

## Features

- status_code, version, and method fields (reason field?)
- CacheControl and WWWAuthenticate types
- Composable URL
- Gzip/deflate support
- Automatic charset/decoding handling
- WSGI compatibility layer (from_wsgi())

## Big features

- Simple select() join
- Client (stateful)
  - Connection pooling
  - Cookie container
  - Pluggable cache
  - Other "session" variables (e.g., referer)
  - Profile (user-agent, browser stuff)
- File upload
- Chardet
- Public Suffix recognition
- Multipart uploads?

## Parser-impacting features

- 100 Continue support (client side first, server side tbd)
- Chunked upload

# Field thoughts

Things fields have:

* name
* attr_name
* duplicate behavior (fold or overwrite)
* from_* methods
* to_bytes method
* documentation
* validation

Question: Which of these are actually more a characteristic of the ValueWrapper (native_type)?

Should "complex" field attributes (i.e., ones with
HeaderValueWrappers, e.g., resp.range) start out with a blank version
of the object, or should they be set to None? Usage will probably
tell; if there's a lot of if checking and/or annoying imports, we can
address it.

- No way to infer scheme (http/https) from what's on the wire :/

## HeaderValueWrappers

- CacheControl
- ContentType
- ContentDisposition
- Cookie
- ETagSet
- UserAgent
- WWWAuthenticate
- Warning
(more)


# Validation thoughts

- Need at least levels (notice/warning/error).
- Operate on Request/Response or RawRequest/RawResponse?

* Basic presence
  * Response.reason should not be blank
* Status code-specific headers
  * Location for redirects
* Unrecognized/unregistered values for certain headers/fields
  * Accept-Ranges: "bytes" or "none"
  * Allow: GET, POST, other known HTTP methods
  * Transfer-Encoding: "chunked"
  * Accept-Encoding/Content-Encoding: identity, gzip, compress, deflate, *
  * Warn on unknown status codes?
* Valid mimetype format for headers using media types
  * Content-Type
  * Content-Disposition
  * Accept
* Unrecognized charset
* URLs missing components (e.g, has a scheme, but no host)
* Length restrictions
  * Warn on long URLs, long cookies

* Maybe: validation for 1.0-compatibility

# State thoughts

A deferred Response has the following states:

- Not started
- Connecting (DNS resolution, opening socket, SSL handshaking)
- Sending request (sending headers, possibly waiting for 100, sending body)
- Waiting
- Receiving response (receiving headers, receiving body/receiving chunks)
- Complete

There may be two or three "complete" states, to represent if the
connection is interupted/terminated (or if the response is cached, but
that probably doesn't need its own state).

As we add features, there are also some higher-level states to
consider, such as:

- Following redirects
- Performing auth roundtrips

Feature: .timings member that records a timestamp for those state transitions.


# Cookie thoughts

- Implement a parser from scratch or use cookielib? (leaning toward the former)
- Haven't quite figured out yet what charset cookies are encoded in?
  Specifiable on a per-cookie basis? Latin-1? Or the same as the page?
- The HTTPHeaderField construct doesn't do great with cookie headers
  because it's perfectly valid and common to have multiple Cookie/Set-Cookie
  headers. Gonna need a special field/hook.


# Other header thoughts

Some common response headers that may be worthy of official fields at
some point:

- Content-Security-Policy
- X-XSS-Protection
- X-Frame-Options
- Access-Control-(Allow-Headers, Allow-Methods, Allow-Origin, Expose-Headers)
- P3P
- X-Powered-By?
- Link (used for favicons?)


# Event thoughts

- Connected (alt: failed, reused)
- Request sent
- Response first byte received
- Headers complete
- Content complete


# Topics

- Why shouldn't Body know about the reader/stream?
- The state of the Client isn't determined only by the parser -> The Joinable interface
- The definition of Complete also changes when lazily fetching bodies
- Nonblocking connects


# Integration questions

- double-check CRLF writing on empty headers
- when a Reader/Writer is done, do we want while True: yield Complete
  or do we want to return/StopIteration?
  - Intentional, for composition of Readers.
- Is * really a valid URL (e.g., "OPTIONS * HTTP/1.1")
