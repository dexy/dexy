#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='dexy',
      version='0.0.1',
      description='Document Automation',
      author='Ana Nelson',
      author_email='ana@ananelson.com',
      url='http://dexy.it',
      packages=find_packages(),
      entry_points = {
          'console_scripts': [
              'dexy = bin.dexy',
          ]
      }
)

