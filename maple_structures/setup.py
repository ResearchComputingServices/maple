'''maple package install through setup'''
from setuptools import setup

setup(
    name="maple-structures",
    version="0.0.1",
    description="A package to hold data structures for news.",
    url="https://github.com/ResearchComputingServices/maple",
    author="Roger Selzler",
    author_email="rogerselzler@cunet.carleton.ca",
    install_requires=['validators'],
    packages=["maple_structures"],
)
