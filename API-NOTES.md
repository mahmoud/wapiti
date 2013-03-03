# API improvement notes #
Some MediaWiki API queries are inconsistent, broken, or otherwise in want of improvement. Similar notes are recorded at [Mediawiki:Requests for comment/API roadmap](http://www.mediawiki.org/wiki/Requests_for_comment/API_roadmap).

* list=usecontribs
    - Docs mention `uccontinue`, but the query uses `ucstart` for continue functionality.
    - `ucprop` should be consistent with `rvprop`: it is missing `flags`, `sha1`, `ids` (parentid)

* missing title
  - Throws a warning `unrecognized parameter`, but it should throw an error.

