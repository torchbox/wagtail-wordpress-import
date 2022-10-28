#!/usr/bin/env python

from os import path

from setuptools import find_packages, setup

from wagtail_wordpress_import import __version__

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "docs/long_description.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="wagtail-wordpress-import",
    version=__version__,
    description="Import XML data into wagtail to create pages and content",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Nick Moreton",
    author_email="nickmoreton@me.com",
    url="https://github.com/torchbox/wagtail-wordpress-import",
    packages=find_packages(),
    include_package_data=True,
    license="BSD",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Framework :: Django",
        "Framework :: Django :: 3.1",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 4.0",
        "Framework :: Django :: 4.1",
        "Framework :: Wagtail",
        "Framework :: Wagtail :: 2",
        "Framework :: Wagtail :: 3",
        "Framework :: Wagtail :: 4",
    ],
    install_requires=[
        "Django>=3.2",
        "Wagtail>=2.15",
        "lxml>=4.7,<4.8",
        "bleach>=4.1,<4.2",
        "prettytable>=2.2,<2.3",
        "shortcodes>=5.1,<6.0",
        "cached-property>=1.5.1,<2.0",
    ],
    extras_require={
        "testing": [
            "freezegun==0.3.15",
            "responses>=0.16.0,<0.17.0",
            "flake8==5.0.4",
            "isort==5.10.1",
            "black==22.10.0",
        ],
    },
    zip_safe=False,
)
