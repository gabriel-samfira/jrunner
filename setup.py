#!/usr/bin/env python

from setuptools import setup, find_packages
import sys
import jrunner

install_requires=[
    'Flask>=0.9',
    'amqp>=1.2.1',
    'netaddr>=0.7.5',
    'oslo.config',
    'eventlet>=0.9.17',
    'iso8601>=0.1.4',
    'redis>=2.6.0',
    'requests>=1.1.0'
],

if sys.version_info < (2,7):
    install_requires=[
        'Flask>=0.9',
        'amqp>=1.2.1',
        'netaddr>=0.7.5',
        'oslo.config',
        'eventlet>=0.9.17',
        'iso8601>=0.1.4',
        'redis>=2.0.0',
        'requests>=1.1.0',
        'importlib>=1.0.2'
    ],

setup(
    name='jrunner',
    version=jrunner.__version__,
    description='Distributed job runner',
    author='Gabriel Adrian Samfira',
    author_email='samfiragabriel@gmail.com',
    url = 'http://cloudbase.it/',
    packages= find_packages(),
    scripts=['jrunner-controller.py', 'jrunner-notify.py', 'jrunner-web.py', 'jrunner-worker.py',],
    classifiers=[
        'Environment :: OpenStack',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 2.6',
    ],
    install_requires=install_requires,
    include_package_data=True,
    zip_safe=False,
)
