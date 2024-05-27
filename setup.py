#!/usr/bin/env python3

import setuptools
from sys import path
path.append("litemapy")  # Import directly from inside the package

from info import LITEMAPY_VERSION

DESCRIPTION = "Read and write Litematica's Minecraft schematics files"


def readme():
    with open("README.md") as f:
        txt = f.read()
    return txt


setuptools.setup(
        name="litemapy",
        version=LITEMAPY_VERSION,
        author="SmylerMC",
        author_email="smyler@mail.com",
        description=DESCRIPTION,
        long_description=readme(),
        long_description_content_type="text/markdown",
        url="https://github.com/SmylerMC/litemapy",
        packages=setuptools.find_packages(exclude=["tests"]),
        license="GNU General Public License v3 (GPLv3)",
        classifiers=[
                "Development Status :: 4 - Beta",
                "Intended Audience :: Other Audience",
                "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
                "Operating System :: OS Independent",
                "Programming Language :: Python :: 3",
                "Topic :: Games/Entertainment",
            ],
        python_requires=">=3.9",
        install_requires=[
                'nbtlib>=2.0.3',
                'typing_extensions',
          ]
    )
