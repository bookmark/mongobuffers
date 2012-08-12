#! /usr/bin/env python
import sys, os
sys.path.append(os.getcwd())

from setuptools import find_packages
from setuptools import setup

__version__ = "0.2"

def main():
    setup(
        name="mongobuffers",
        version=__version__,
        description='''An implementation of Google's protocol buffers using mongo as a datastore.''',
        long_description='''An implementation of Google's protocol buffers using mongo as a datastore.
        ''',
        author="Nate Skulic",
        author_email="nate.skulic@gmail.com",
        url="http://code.google.com/p/mongobuffers",
        download_url="http://code.google.com/p/mongobuffers/downloads/list",
        license="Apache License (2.0)",
        packages=find_packages(),
        install_requires=['pymongo', 'sphinx'],
        data_files=[],
        package_dir={'mongobuffers': 'mongobuffers'},
        classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'License :: OSI Approved :: Apache Software License',
        ]
    )

if __name__ == '__main__':
    main()
