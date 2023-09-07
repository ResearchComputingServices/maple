'''maple_interface package'''
from setuptools import setup

setup(
    name="maple-interface",
    version="0.0.1",
    description="Package to communicate with backend.",
    url="https://github.com/ResearchComputingServices/maple/maple_interface",
    author="RCS Team",
    author_email="rogerselzler@cunet.carleton.ca",
    install_requires=['requests'],
    packages=["maple_interface"],
)
