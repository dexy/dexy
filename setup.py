#!/usr/bin/env python

from setuptools import setup, find_packages
from dexy.version import VERSION

setup(name='dexy',
      version=VERSION,
      description='Document Automation',
      author='Ana Nelson',
      author_email='ana@ananelson.com',
      url='http://dexy.it',
      packages=find_packages(),
      entry_points = {
          'console_scripts' : [
              'dexy = dexy.interface:dexy_command',
              'dexy-live-server = dexy.interface:dexy_live_server'
          ]
      },
      install_requires = [
          'pexpect',
          'jinja2',
          'pygments',
          'idiopidae', #TODO remove dependency
          'zapps', #TODO remove dependency
          'ordereddict' # only used for Python < 2.7, otherwise ignored
      ],
      extras_require = {
          'liveserver': ['cssutils', 'BeautifulSoup', 'pynliner', 'ansi2html']
      },
      dependency_links = [ "http://dexy.it/external-dependencies/" ]
)

