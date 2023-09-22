'''maple_config package'''
from setuptools import setup

setup(
    name="maple-config",
    version="0.0.1",
    description="Package to load configuration for maple project.",
    url="https://github.com/ResearchComputingServices/maple/maple_interface",
    author="RCS Team",
    author_email="rogerselzler@cunet.carleton.ca",
    install_requires=['python-dotenv'],
    packages=["maple_config"],
)
