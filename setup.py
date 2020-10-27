#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = ['numpy', 'tqdm', 'Pillow', ]

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest>=3', ]

setup(
    author="Tim Parker",
    author_email='tim.parkerd@gmail.com',
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
    ],
    description="Utility library for consuming and manipulating x-ray data in RAW format",
    entry_points={
        'console_scripts': [
            'raw-convert=rawtools.cli:raw_convert',
            'raw-generate=rawtools.cli:raw_generate',
            'raw-nsihdr=rawtools.cli:raw_nsihdr',
            'raw2img=rawtools.cli:raw_image',
            'raw-qc=rawtools.cli:raw_qc'
        ],
    },
    install_requires=requirements,
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='rawtools',
    name='rawtools',
    packages=find_packages(include=['rawtools', 'rawtools.*']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/tparkerd/python-rawtools',
    version='0.1.3',
    zip_safe=False,
)
