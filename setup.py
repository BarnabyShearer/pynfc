""""""
from setuptools import setup
from os import path

with open(path.join(path.abspath(path.dirname(__file__)), "README.rst")) as f:
    long_description = f.read()

from setuptools.command.build_py import build_py

class Build(build_py):

    def run(self):
        # Import after setuptools has downloaded dependencies
        from gen import run
        run()
        return build_py.run(self)

setup(
    name="pynfc",
    version="0.1.2",
    description="`ctypeslib` converted libnfc and libfreefare",
    long_description=long_description,
    author="Barnaby Shearer",
    author_email="b@Zi.iS",
    url="https://github.com/BarnabyShearer/pynfc.git",
    license="BSD",
    keywords="RFID NFC Mifare Desfire",
    packages=[
        "pynfc"
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3"
    ],
    cmdclass={
        "build_py": Build
    },
    setup_requires=["pytest-runner", "clang==5.*", "ctypeslib2"],
    tests_require=["pytest"]
)
