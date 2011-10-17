#!/usr/bin/env python

from setuptools import setup, find_packages
from dexy.version import Version

setup(name='dexy',
      version=Version.VERSION,
      description='Document Automation',
      author='Ana Nelson',
      author_email='ana@ananelson.com',
      url='http://dexy.it',
      packages=find_packages(),
      include_package_data = True,
      install_requires = [
          'ansi2html',
          'cssutils',
          'idiopidae',
          'jinja2',
          'python-modargs==1.2',
          'nose',
          'ordereddict',
          'pexpect',
          'pygments',
          'pynliner',
          'zapps',

          # lock down versions of ansi2html dependencies
          'BeautifulSoup==3.2.0'

      ],
      entry_points = {
          'console_scripts' : [
              'dexy = dexy.commands:run'
          ]
      },
      dependency_links = [ "http://dexy.it/external-dependencies/" ]
)

