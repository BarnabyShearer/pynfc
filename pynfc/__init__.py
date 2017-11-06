"""
ctypeslib converted libnfc and libfreefare with just enough of the interals to actually be usable.

>>> import pynfc
>>> n = pynfc.Nfc("pn532_uart:/dev/ttyFake:115200")
Traceback (most recent call last):
    ...
Exception: Couldn't nfc_open (comms?)
"""

import os
try:
    import queue
except ImportError:
    import Queue as queue
import threading
import ctypes
from . import nfc, freefare, mifare

class TimeoutException(Exception):
    """Timeout Exception"""
    pass

class Timeout(object):
    """Watchdog to timeout functions"""

    def __init__(self, timeoutlength=1):
        """Leng in secconds"""
        self.timeoutlength = timeoutlength

    def __call__(self, func):
        """Wrap the all"""
        def wrapped_f(*args, **kwargs):
            """Wrapped function"""
            timeout_queue = queue.Queue()
            tread = threading.Thread(target=lambda: timeout_queue.put(func(*args, **kwargs)))
            tread.daemon = True
            tread.start()
            tread.join(self.timeoutlength)
            if tread.is_alive():
                ctypes.pythonapi.PyThreadState_SetAsyncExc(
                    ctypes.c_long(tread.ident),
                    ctypes.py_object(SystemExit)
                )
                raise TimeoutException("Timeout", func)
            return timeout_queue.get()
        return wrapped_f

poll = Timeout(None)(nfc.nfc_initiator_poll_target) #pylint: disable-msg=invalid-name
get_tags = Timeout()(freefare.freefare_get_tags) #pylint: disable-msg=invalid-name
desfire_connect = Timeout()(freefare.mifare_desfire_connect) #pylint: disable-msg=invalid-name
desfire_auth = Timeout()(freefare.mifare_desfire_authenticate) #pylint: disable-msg=invalid-name
classic_connect = Timeout()(freefare.mifare_classic_connect) #pylint: disable-msg=invalid-name
classic_auth = Timeout()(freefare.mifare_classic_authenticate) #pylint: disable-msg=invalid-name

class Nfc(object):
    """A slightly pythonic interface"""

    pctx = None
    pdevice = None

    def __init__(self, device=None, log_level=None):
        """Connect to libnfc"""
        if log_level is not None:
            os.environ["LIBNFC_LOG_LEVEL"] = str(log_level)
        if device is not None:
            os.environ["LIBNFC_DEFAULT_DEVICE"] = device
        self.pctx = nfc.nfc_init.argtypes[0]._type_() #pylint: disable-msg=protected-access
        nfc.nfc_init(ctypes.byref(self.pctx)) #Mallocs the ctx
        if not self.pctx:
            raise Exception("Couldn't nfc_init (malloc?)")
        self.pdevice = nfc.nfc_open(self.pctx, None)
        if not self.pdevice:
            raise Exception("Couldn't nfc_open (comms?)")

    def poll(self, modulations=((nfc.NMT_ISO14443A, nfc.NBR_424),), times=0xFF, delay=1):
        """Wait for device to enter field"""
        #pylint: disable-msg=protected-access
        _modulations = (
            nfc.nfc_initiator_poll_target.argtypes[1]._type_ * len(modulations)
        )()
        for i, (nmt, nbr) in enumerate(modulations):
            _modulations[i].nmt = nmt
            _modulations[i].nbr = nbr
        target = nfc.nfc_initiator_poll_target.argtypes[5]._type_()
        while True:
            numdev = poll(
                self.pdevice,
                ctypes.byref(_modulations[0]),
                len(_modulations),
                times,
                delay,
                ctypes.byref(target)
            )
            if numdev <= 0:
                return
            #Freefare dosn't like nfc's target
            ptarget = get_tags(self.pdevice).contents
            if not ptarget:
                continue
            ret = Target(ptarget)
            if ret.type == freefare.DESFIRE:
                ret = Desfire(ptarget)
            elif ret.type == freefare.CLASSIC_1K or ret.type == freefare.CLASSIC_4K:
                ret = Mifare(ptarget)
            yield ret
            freefare.freefare_free_tags(ptarget)

    def __del__(self):
        """Terminate comms with reader cleanly"""
        if self.pdevice:
            nfc.nfc_close(self.pdevice)
        nfc.nfc_exit(self.pctx)

class Target(object):
    """Interface repersenting targets devices that may enter our field"""

    def __init__(self, target):
        """New target device"""
        self.target = target

    @property
    def uid(self):
        """
        The UID of the device
        (can vary in length based on type)
        (do not rely on them being absolutly unique)
        """
        return freefare.freefare_get_tag_uid(self.target).decode('ascii')

    @property
    def type(self):
        """Type of this device"""
        return freefare.freefare_get_tag_type(self.target)

class Desfire(Target):
    """Specilise for DesFire devices"""

    def auth(self, key, keyno=0):
        """Authenticate"""
        if desfire_connect(self.target) != 0:
            return False
        if len(key) == 8:
            key = (ctypes.c_ubyte * 8)(*bytearray(key))
            desfire_key = freefare.mifare_desfire_des_key_new_with_version(key)
        else:
            key = (ctypes.c_ubyte * 16)(*bytearray(key))
            desfire_key = freefare.mifare_desfire_aes_key_new_with_version(key, 1)
        ret = desfire_auth(self.target, keyno, desfire_key)
        freefare.mifare_desfire_key_free(desfire_key)
        return ret == 0

class Mifare(Target):
    """Specilise for Mifare devices"""

    def auth(self, data, sector=1, akey=True):
        """Authenticate"""
        if classic_connect(self.target) != 0:
            return False
        block = freefare.mifare_classic_sector_last_block(sector)
        auth_tag = mifare.mifare_classic_tag.from_buffer_copy(data)
        if akey:
            ret = classic_auth(
                self.target,
                block,
                auth_tag.amb[block].mbt.abtKeyA,
                freefare.MFC_KEY_A
            )
        else:
            ret = classic_auth(
                self.target,
                block,
                auth_tag.amb[block].mbt.abtKeyB,
                freefare.MFC_KEY_B
            )
        return ret == 0
