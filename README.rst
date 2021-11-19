=====
pynfc
=====
.. image:: https://readthedocs.org/projects/pynfc/badge/?version=latest
    :target: https://pynfc.readthedocs.io/en/latest/?badge=latest

.. image:: https://badge.fury.io/py/pynfc.svg
    :target: https://badge.fury.io/py/pynfc

`ctypeslib` converted libnfc and libfreefare.

Install
-------

::

    sudo apt install libclang-dev libfreefare-dev
    python3 -m pip install pynfc

Usage
-----
::

    from pynfc import Nfc, Desfire, Timeout
    
    n = Nfc("pn532_uart:/dev/ttyUSB0:115200")
    
    DESFIRE_DEFAULT_KEY = b'\x00' * 8
    MIFARE_BLANK_TOKEN = b'\xFF' * 1024 * 4
    
    for target in n.poll():
        try:
            print(target.uid, target.auth(DESFIRE_DEFAULT_KEY if type(target) == Desfire else MIFARE_BLANK_TOKEN))
        except TimeoutException:
            pass

Develop
-------
::

    sudo apt install libfreefare-dev libclang-5.0-dev
    git clone https://github.com/BarnabyShearer/pynfc.git
    cd pynfc
    python3 setup.py develop --user

