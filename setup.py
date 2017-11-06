""""""
from setuptools import setup
from os import path

with open(path.join(path.abspath(path.dirname(__file__)), 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="pynfc",
    version="0.0.3",
    description="`ctypeslib` converted libnfc and libfreefare",
    long_description=long_description,
    author="Barnaby Shearer",
    author_email="b@Zi.iS",
    url="https://github.com/BarnabyShearer/pynfc.git",
    license='BSD',
    keywords="RFID NFC Mifare Desfire",
    packages=[
        "pynfc"
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3"
    ],
    install_requires=[
        "psutil"
    ]
)
