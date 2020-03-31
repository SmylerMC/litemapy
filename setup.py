#!/usr/bin/env python3

import setuptools

DESCRIPTION = "Read and write Litematica's Minecraft schematics files"
setuptools.setup(
        name="litemapy",
        version="0.1.0a0",
        author="SmylerMC",
        author_email="smyler@mail.com",
        description=DESCRIPTION,
        long_description=DESCRIPTION, #TODO
        url="https://github.com/SmylerMC/litemapy",
        packages=setuptools.find_packages(),
        license="GNU General Public License v3 (GPLv3)",
        classifiers=[
                "Development Status :: 3 - Alpha",
                "Intended Audience :: Other Audience",
                "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
                "Operating System :: OS Independent",
                "Programming Language :: Python :: 3",
                "Topic :: Games/Entertainment",
            ],
        python_requires=">=3.5",
        install_requires=[
                'nbtlib',
          ],
        test_suite="tests",
    )
