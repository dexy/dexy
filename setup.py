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
      scripts = ['bin/dexy']
)

