'''maple_interface package'''
from setuptools import setup

setup(
    name="maple-chatgpt",
    version="0.0.1",
    description="Package with socketio async server and client to control chatgpt requests..",
    url="https://github.com/ResearchComputingServices/maple/maple_chatgpt",
    author="RCS Team",
    author_email="rogerselzler@cunet.carleton.ca",
    install_requires=['requests'],
    packages=["maple_chatgpt"],
)
