import re
from pathlib import Path

from setuptools import setup, find_packages


with open("README.md", "r") as f:
    long_description = f.read()

txt = (Path(__file__).parent / 'aiotodoist' / '__init__.py').read_text('utf-8')
version = re.findall(r"^__version__ = '([^']+)'\r?", txt, re.M)[0]

setup(
    name="aiotodoist",
    version=version,
    author="Lanfon",
    author_email="lanfon72@gmail.com",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/LFLab/aio-todoist",
    packages=find_packages(),
    install_requires=["aiohttp>=3.*, <4.*", "todoist-python>=8.*"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9'
    ],
    python_requires='>=3.7',
)
