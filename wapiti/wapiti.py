# -*- coding: utf-8 -*-
from __future__ import unicode_literals


'''
The beginnings of a better Mediawiki API library (with certain builtin
affordances for the more popular wikis and extensions). Most of what
you see below is implementation internals, the public API isn't set yet,
but check back soon.

# TODO
 * Create client class
 * Port more API calls
 * Support namespace filtering in a general fashion
 * Retry and timeout behaviors
 * Get my shit together and continue work on the HTTP client.
 * Automatically add 'g' to prefix if static_params has key 'generator'
 * Underscoring args
 * Support lists of static params (which are then joined automatically)
 * pause/resume
 * better differentiation between the following error groups:
   * Network/connectivity
   * Logic
   * Actual Mediawiki API errors ('no such category', etc.)
 * Relatedly: Save MediaWiki API warnings

Types of API calls:
 * single argument -> multiple results (get category)
 * many arguments -> up to one result per argument (get protections)
 * multiple arguments -> multiple results per argument (get language links)
   * TODO: establish return format convention for this

Need generic support for:
 * Talk -> respective namespace mapping
 * APIs which support both pageid and title lookup
 * Redirect following
 * Namespace filtering
'''
