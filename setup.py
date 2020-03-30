#!/usr/bin/env python3

import setuptools

DESCRIPTION = "Read and write Litematica's Minecraft schematics files"
setuptools.setup(
        name="litemapy",
        version="0.0.1.dev0",
        author="SmylerMC",
        author_email="smyler@mail.com",
        description=DESCRIPTION,
        long_description=DESCRIPTION, #TODO
        url="https://github.com/SmylerMC/litemapy",
        packages=setuptools.find_packages(),
        classifiers=[], #TODO
        python_requires=">=3.5" #TODO,
    )
