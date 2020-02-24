#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import setuptools
from auto_ovpn.version import get_version


with open("README.md", "r") as myfile:
    long_description = myfile.read()

setuptools.setup(
    name="auto_ovpn",
    version=get_version(save_json=True)["version"],
    author="Jorge Sacristan",
    author_email="j.sacris@gmail.com",
    description="A package to automatically create OpenVPN files (*.ovpn) issued by a CA.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jsacrist/auto-ovpn.git",
    packages=setuptools.find_packages(exclude=("build", "dist", "*.egg-info")),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: GPLv3 License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "auto-ovpn=auto_ovpn.cli:main",
        ]
    },
    install_requires=[
        "pyyaml>=3.11",
        "jinja2>=2.10",
        "gitpython>=3.0.8",
    ],
)
