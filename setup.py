#!/usr/bin/env python
"""The setup script."""
from __future__ import annotations

import platform

from setuptools import find_packages
from setuptools import setup

with open('README.md') as readme_file:
    readme = readme_file.read()

with open('HISTORY.md') as history_file:
    history = history_file.read()

with open('requirements.txt') as requirements_file:
    requirements = requirements_file.readlines()

setup_requirements = [
    'pytest-runner',
]

test_requirements = [
    'pytest>=3',
]

description = (
    'Utility library for consuming and manipulating x-ray data in',
    'RAW format',
)

# Determine the correct platform
system = platform.system()
arch, _ = platform.architecture()
if system == 'Linux':
    if arch == '64bit':
        efxsdk = 'lib/linux64/efX-SDK.so'
    else:
        efxsdk = 'lib/linux32/efX-SDK.so'
if system == 'Windows':
    efxsdk = 'lib/win32/efX-SDK.dll'
if system == 'Darwin':
    efxsdk = 'lib/mac32/efX-SDK'

setup(
    author='Tim Parker',
    author_email='tparker@danforthcenter.com',
    python_requires='>=3.9',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
    ],
    description=description,
    entry_points={
        'console_scripts': [
            'raw-convert=rawtools.convert:main',
            'raw-generate=rawtools.generate:main',
            'nsihdr2raw=rawtools.nsihdr:main',
            'raw2img=rawtools.raw2img:main',
            'raw-qc=rawtools.qualitycontrol:main',
            'img2pcd=rawtools.img2pcd:main',
        ],
    },
    install_requires=requirements,
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    package_data={'efxsdk': [efxsdk]},
    keywords='rawtools',
    name='rawtools',
    packages=find_packages(include=['rawtools', 'rawtools.*']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/Topp-Roots-Lab/python-rawtools',
    version='0.6.0',
    zip_safe=False,
)
