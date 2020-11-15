#!/usr/bin/python

from setuptools import setup
from setuptools import find_packages


def get_version():
    with open("getmymsg/__init__.py") as f:
        for line in f:
            if line.startswith("__version__"):
                return eval(line.split("=")[-1])


with open("README.md", "r") as readme_file:
    readme = readme_file.read()

setup(
    name="getmymsg",
    version=get_version(),
    description="Servidor de práctica 3 de curso de Sistemas Distribuidos.",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="Rómulo Rodríguez",
    author_email="rodriguezrjrr@gmail.com",
    license="GPLv3",
    url="https://gitlab.com/ucab-ds/getmymsg",
    python_requires='>=2.7',
    packages=find_packages(),
    install_requires=[
        "PyYAML>=5.3.1",
    ],
    entry_points={
        "console_scripts": [
            "getmymsg-server = getmymsg:main",
        ]
    },
)
