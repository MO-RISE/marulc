import io
import os
import sys
import codecs

from setuptools import find_packages, setup, Command

# Package meta-data.
NAME = "morise-jasmine"
DESCRIPTION = "NMEA 0183 and 2000 parser"

URL = "https://github.com/rise-mo/jasmine"
EMAIL = "fredrik.x.olsson@ri.se"
AUTHOR = "RISE Research Institute of Sweden"
REQUIRES_PYTHON = ">=3.7.0"
VERSION = "0.2.0"

# Long description
def read(fname):
    file_path = os.path.join(os.path.dirname(__file__), fname)
    return codecs.open(file_path, encoding="utf-8").read()


LONG_DESCRIPTION = read("README.md")

# What packages are required for this module to be executed?
# Parse the requirements-txt file and use for install_requires in pip
with open("requirements.txt") as f:
    REQUIRED = f.read().splitlines()

# What packages are optional?
EXTRAS = {
    # 'fancy feature': ['django'],
}

# Trove classifiers (i.e. metadata) for package discovery.
# Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
TROVE_CLASSIFIERS = [
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.7",
]

# Here be dragons
# ---------------

setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    author=AUTHOR,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),
    package_data={"": ["*.json"]},
    install_requires=REQUIRED,
    extras_require=EXTRAS,
    include_package_data=True,
    license="MIT",
    classifiers=TROVE_CLASSIFIERS,
)
