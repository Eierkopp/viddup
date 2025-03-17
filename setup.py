#!/usr/bin/python3

from setuptools import setup

setup(
    name="viddup",
    version="2.5",
    description="Simple video hashing and similarity detection tool",
    author="Eierkopp",
    packages=["viddup"],
    # scripts=["bin/viddup"],
    author_email="depp@eierkopp.ddnss.org",
    install_requires=[
        "annoy",
    ],
)
