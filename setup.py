"""
    Wapiti
    ~~~~~~

    Wapiti is a Wikipedia API client focused on providing a consistent
    and performant abstraction around the widely varying Mediawiki API
    endpoints and data models. Read-only APIs are first priority, but
    write operations are on the way. See `the Github project
    <https://github.com/mahmoud/wapiti>`_ for more info.

    :copyright: (c) 2013 by Mahmoud Hashemi and Stephen LaPorte
    :license: BSD, see LICENSE for more details.

"""

import sys
from setuptools import setup


__author__ = 'Mahmoud Hashemi'
__version__ = '0.1'
__contact__ = 'mahmoudrhashemi@gmail.com'
__url__ = 'https://github.com/mahmoud/wapiti'
__license__ = 'BSD'


if sys.version_info >= (3,):
    raise NotImplementedError("wapiti Python 3 support en route to your location")


setup(name='wapiti',
      version=__version__,
      description="A Wikipedia API client for humans and elk.",
      long_description=__doc__,
      author=__author__,
      author_email=__contact__,
      url=__url__,
      packages=['wapiti', 'wapiti.operations'],
      include_package_data=True,
      zip_safe=False,
      license=__license__,
      platforms='any',
      classifiers=[
          'Intended Audience :: Developers',
          'Topic :: Software Development :: Libraries',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Topic :: Internet :: WWW/HTTP',
          'Topic :: Education',
          'Development Status :: 3 - Alpha']
      )
