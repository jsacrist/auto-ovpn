#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import setuptools
import auto_ovpn as pkg


with open("README.md", "r") as myfile:
    long_description = myfile.read()

with open("install_requires.txt", "r") as myfile:
    install_requires = myfile.read()

setuptools.setup(
    name=pkg.name,
    version=pkg.version.get_version(save_json=True)["version"],
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
    scripts=[
        "scripts/auto-ovpn-version.sh",
        "scripts/auto-ovpn-version.py",
    ],
    install_requires=install_requires,
)
