# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='spudbin',
    version='0.1',
    description='Potato tracker',
    author='Thomas Lant',
    author_email='lampholder@gmail.com',
    url='https://github.com/lampholder/spudbin',
    packages=find_packages(exclude=('tests', 'docs'))
    #package_data={'': ['*.json', '*.csv', '*.yaml']},
    #scripts=['bin/report.py', 'bin/metrics.py']
)
