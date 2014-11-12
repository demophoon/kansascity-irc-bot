#!/usr/bin/env python
# encoding: utf-8

from setuptools import setup

setup(
    name = "#r/kansascity Bot",
    version = "1.0.0",
    author = "Britt Gresham and Contributors",
    author_email = "brittcgresham@gmail.com",
    description = ("A bot for doing things in the IRC"),
    license = "MIT",
    install_requires=[
        "sqlalchemy",
        "nltk",
        "numpy",
        "pyyaml",
        "pylast",
    ],
)
