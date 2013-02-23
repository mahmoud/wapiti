wapiti
======

![Wapiti](http://upload.wikimedia.org/wikipedia/commons/thumb/5/59/Elk_1_%28PSF%29.png/212px-Elk_1_%28PSF%29.png)

A MediaWiki API wrapper in Python for humans and elk. 

Wapiti makes it simple for python scripts to retrieve data from [Wikipedia](https://en.wikipedia.org/w/api.php). No more worries about query limits, continue strings, or formatting. Just ask for  data and get structured results.

Example
-------
Let's say you wanted to get the members of Wikipedia's [Category:Lists of superlatives](http://en.wikipedia.org/wiki/Category:Lists_of_superlatives). First, initialize a `WapitiClient` and change any settings. Next, run the operation `get_category_pages` on the category `'Lists of superlatives'`, with a limit of `10`:

```python
import wapiti
client = wapiti.WapitiClient()
superlative_category_pages = client.get_category_pages_recursive('Lists of superlatives', 10)
```

This returns a list of `PageIdentifiers` for the category members:

```python
[PageIdentifier(u'Ranked lists of Chilean regions', 25042332, 0, u'enwp'),
 PageIdentifier(u'List of the heaviest people', 3626619, 0, u'enwp'),
 PageIdentifier(u'List of heaviest bells', 25636339, 0, u'enwp'),
 PageIdentifier(u'List of elevation extremes by country', 24285393, 0, u'enwp'),
 PageIdentifier(u'List of automotive superlatives', 858694, 0, u'enwp'),
 PageIdentifier(u'Extremes on Earth', 736240, 0, u'enwp'),
 PageIdentifier(u'List of highest paid Major League Baseball players', 224893, 0, u'enwp'),
 PageIdentifier(u'List of fastest production motorcycles', 32140340, 0, u'enwp'),
 PageIdentifier(u'Angus Maddison statistics of the ten largest economies by GDP (PPP)', 38385899, 0, u'enwp'),
 PageIdentifier(u'List of fastest production motorcycles by acceleration', 34443631, 0, u'enwp')]
```

Operations
----------
Operations usually take two positional arguments: the `query_param` (page, category, template, etc.), and `limit` (maximum number of results).

- `get_random(limit)` : returns a list of `PageIdentifiers` for random pages.
- `get_category_pages(category, limit)` : returns a list of `PageIdentifiers` for the articles or talk pages in a category. If you are interested in getting pages beyond of the main and talk namespace, try `get_category`.
- `get_category_pages_recursive(category, limit)` : returns a list of `PageIdentifiers` for the articles or talk pages in a category and its subcategories. If you are interested in getting pages beyond of the main and talk namespace, try `get_category_recursive`.
- `get_transcludes(page, limit)` : returns a list of `PageIdentifiers` for the articles that embed (transclude) a page. For example, see the pages that embed [Template:Infobox](http://en.wikipedia.org/wiki/Special:WhatLinksHere/Template:Infobox) with `client.get_transcludes('Infobox')`.
- `get_backlinks(page, limit)` : returns a list of `PageIdentifiers` for pages that internally link back to a page. For example, see the pages that [link to 'Coffee'](http://en.wikipedia.org/wiki/Special:WhatLinksHere/Coffee) with `client.get_backlinks('Coffee')`.
- `get_revision_infos(page, limit)` : returns a list of `RevisionInfos` for a page's revisions.
- `get_current_content(page, limit)` : returns a list of `Revisions` (including text content) for the page's most recent revisions.

Other operations are available: see wapiti/operations

Models
------
Models describe the structure for result data. For the full list of models, see wapiti/operations/models.py

### PageIdentifier ###
A `PageIdentifier` describes the standard information available for a  page.

- **Title** : unique name of the page
- **ID** : the primary key for the page
- **Namespace** : the [namespace](http://en.wikipedia.org/wiki/Wikipedia:Namespace) number, which can indicate whether the page is an article, discussion page, user page, template, category, etc.
- **Source** : the MediaWiki API where this page was retrieved
- **Normalized title** : the title may have been normalized by MediaWiki, for example, by resolving a redirect
- **Subject ID** : the ID of the corresponding page in the basic namespace
- **Talk page ID** : the ID of the corresponding page in the [talk namespace](http://en.wikipedia.org/wiki/Help:Using_talk_pages)

### RevisionInfo ###
A `RevisionInfo` describes the standard information for a revision.

* **PageIdentifier** : the page's `PageIdentifier`
* **Subject revision ID** : the primary key for a revision
* **Parent revision ID** : the previous revision to the page
* **User text** : the editor's username, or IP address for an unregistered user
* **User ID** : the unique id of the user who submitted this revision. It may be 0 for an unregistered user.
* **Size** : the length of the article at this revision
* **Timestamp** : timestamp in UTC when this revision was submitted
* **SHA1** : the SHA-1 hash of revision text in base-36.
* **Edit summary** : the [edit summary](http://meta.wikimedia.org/wiki/Help:Edit_summary) (or 'comment') for a contribution. In some cases, it may have been deleted (or 'oversighted') and unavailable through the API.
* **Tags** : brief messages that MediaWiki (or an extension) may automatically place next to certain edits. [Tags](http://en.wikipedia.org/wiki/Wikipedia:Tags) are not common, usually placed by Edit Filter or VisualEditor extensions.
* **Parsed** : whether the page is parsed (html) or not (wikitext)

### Revision ###
A `Revision` includes the same data as `RevisionInfo`, plus full text content.

todo
----
- Logging
- Client settings
- Port more API calls
- Retry and timeout behaviors
- Get my shit together and continue work on the HTTP client.
- Underscoring args
- Pause/resume
- Better differentiation between the following error groups:
   * Network/connectivity
   * Logic
   * Actual Mediawiki API errors ('no such category', etc.)
- Relatedly: Save MediaWiki API warnings
- Types of API calls:
   * single argument -> multiple results (get category)
   * many arguments -> up to one result per argument (get protections)
   * multiple arguments -> multiple results per argument (get language links)
   * TODO: establish return format convention for this
- Need generic support for:
   * APIs which support both pageid and title lookup
   * Redirect following
- Full docs
