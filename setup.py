"""A setuptools based setup module.
See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages

# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# We now define the version number in __init__.py
# Here we can't use import as that would
# tell us the version of Biopython already installed (if any).
__version__ = "Undefined"
for line in open("kamaji/__init__.py"):
    if line.startswith("__version__"):
        exec(line.strip())

setup(
    name="kamaji",
    version=__version__,
    description="Tool for organizing and renaming photos",
    url="https://github.com/sbliven/kamaji",
    author="Spencer Bliven",
    author_email="spencer.bliven@gmail.com",
    license="GPL 3.0",
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: GPL 3.0",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    keywords="photo organization directory management",
    packages=find_packages(exclude=["contrib", "docs", "tests"]),
    install_requires=[],
    setup_requires=["pytest-runner >= 2"],
    tests_require=["pytest >= 3", "tox >= 3", "flake8 >= 3"],
)
