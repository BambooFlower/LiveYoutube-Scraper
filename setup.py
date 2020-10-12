# -*- coding: utf-8 -*-
import os
from setuptools import setup, find_packages

required_modules = ['requests', 'python-dateutil', 'six', 'cached-property']

version = '1.0.3'

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as file:
    long_description = file.read()

setup(
    name="YTLiveScrape", 
    packages=find_packages(exclude=('examples')),
    version=version ,
    description="Simple YouTube Live scrape package",
    license='MIT',
    author = 'Chelyabinsk',
    author_email = '15384813+chelyabinsk@users.noreply.github.com',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/BambooFlower/LiveYoutube-Scraper",
    download_url = 'https://github.com/BambooFlower/LiveYoutube-Scraper/archive/v1.0.3.tar.gz',
    keywords=["YouTube", "Live comments","scrape"],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        "Programming Language :: Python :: 3",
        'Topic :: Software Development :: Build Tools',
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
