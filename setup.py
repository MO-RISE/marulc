import io
import os
import sys

from setuptools import find_packages, setup, Command

# Package meta-data.
NAME = 'TODO'
DESCRIPTION = 'TODO'

URL = 'https://github.com/rise-mo/TODO'
EMAIL = 'TODO'
AUTHOR = 'Rise Maritime Operations'
REQUIRES_PYTHON = '>=3.7.0'
VERSION = '0.1.0'

# What packages are required for this module to be executed?
REQUIRED = [
    # 'numpy', 'pandas',
]

# What packages are optional?
EXTRAS = {
    # 'fancy feature': ['django'],
}

# Trove classifiers (i.e. metadata) for package discovery.
# Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
TROVE_CLASSIFIERS = [
  'Programming Language :: Python',
  'Programming Language :: Python :: 3',
  'Programming Language :: Python :: 3.7',
]

# Here be dragons
# ---------------

setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type='text/markdown',
    author=AUTHOR,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),
    install_requires=REQUIRED,
    extras_require=EXTRAS,
    include_package_data=True,
    license='MIT',
    classifiers=TROVE_CLASSIFIERS,
)
