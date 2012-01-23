#!/usr/bin/env python

from setuptools import setup, find_packages
from dexy.version import Version

setup(name='dexy',
      author='Ana Nelson',
      author_email='ana@ananelson.com',
      description='Document Automation',
      include_package_data = True,
      packages=find_packages(),
      package_data = { "dexy" : ["ext/*"] },
      url='http://dexy.it',
      version=Version.VERSION,
      install_requires = [
          'idiopidae>=0.5.1',
          'jinja2',
          'nose',
          'ordereddict', # for Python 2.6
          'pexpect',
          'pygments',
          'python-modargs>=1.2',
          'zapps'
      ],
      entry_points = {
          'console_scripts' : [
              'dexy = dexy.commands:run'
          ]
      },
      dependency_links = [ "http://dexy.it/external-dependencies/" ]
)

