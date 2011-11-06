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

