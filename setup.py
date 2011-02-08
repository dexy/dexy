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
      extras_require = {
          'py26' : ['ordereddict'],
          'common' : ['pexpect', 'jinja2', 'pygments', 'idiopidae', 'zapps'],
          'liveserver': ['cssutils', 'BeautifulSoup', 'pynliner', 'ansi2html']
      },
      dependency_links = [ "http://dexy.it/external-dependencies/" ]
)

