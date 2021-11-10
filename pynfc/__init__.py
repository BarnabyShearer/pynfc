"""Libnfc and libfreefare with just enough of the interals to actually be usable."""

import ctypes
import os
import threading
from typing import Any, Callable, Iterator, Optional, Tuple, TypeVar

from . import nfc  # type: ignore

try:
    import queue
except ImportError:
    import Queue as queue  # type: ignore  # noqa: N813


class TimeoutException(Exception):
    """Timeout Exception."""

    pass


T = TypeVar("T", bound=Callable[..., Any])


class Timeout(object):
    """Watchdog to timeout functions."""

    def __init__(self, timeoutlength=1):
        # type: (Optional[int]) -> None
        """Length in secconds."""
        self.timeoutlength = timeoutlength

    def __call__(self, func):
        # type: (T) -> T
        """Wrap the call."""

        def wrapped_f(*args, **kwargs):
            # type: (*Any, **Any) -> Any
            """Wrap function."""
            timeout_queue = queue.Queue()  # type: queue.Queue[T]
            thread = threading.Thread(
                target=lambda: timeout_queue.put(func(*args, **kwargs))
            )
            thread.daemon = True
            thread.start()
            thread.join(self.timeoutlength)
            if thread.is_alive() and thread.ident:
                ctypes.pythonapi.PyThreadState_SetAsyncExc(
                    ctypes.c_long(thread.ident), ctypes.py_object(SystemExit)
                )
                raise TimeoutException("Timeout", func)
            return timeout_queue.get()

        return wrapped_f  # type: ignore


poll = Timeout(None)(nfc.nfc_initiator_poll_target)
tag_new = Timeout()(nfc.freefare_tag_new)
desfire_connect = Timeout()(nfc.mifare_desfire_connect)
desfire_auth = Timeout()(nfc.mifare_desfire_authenticate)
classic_connect = Timeout()(nfc.mifare_classic_connect)
classic_auth = Timeout()(nfc.mifare_classic_authenticate)


class Nfc(object):
    """A slightly pythonic interface."""

    pctx = None
    pdevice = None

    def __init__(self, device=None, log_level=None):
        # type: (Optional[str], Optional[str]) -> None
        """Connect to libnfc."""
        if log_level is not None:
            os.environ["LIBNFC_LOG_LEVEL"] = str(log_level)
        if device is not None:
            os.environ["LIBNFC_DEFAULT_DEVICE"] = device
        self.pctx = ctypes.POINTER(nfc.struct_nfc_context)()
        nfc.nfc_init(self.pctx)  # Mallocs the ctx
        if not self.pctx:
            raise Exception("Couldn't nfc_init (malloc?)")
        nfc.nfc_open.argtypes = [
            ctypes.POINTER(nfc.struct_nfc_context),
            ctypes.POINTER(ctypes.c_char),
        ]
        self.pdevice = nfc.nfc_open(self.pctx, None)
        if not self.pdevice:
            raise Exception("Couldn't nfc_open (comms?)")

    def poll(
        self, modulations=((nfc.NMT_ISO14443A, nfc.NBR_424),), times=0xFF, delay=1
    ):
        # type: (Tuple[Tuple[int, int]], int, int) -> Iterator[Target]
        """Wait for device to enter field."""
        _modulations = (nfc.nfc_modulation * len(modulations))()
        for i, (nmt, nbr) in enumerate(modulations):
            _modulations[i].nmt = nmt
            _modulations[i].nbr = nbr
        target = nfc.nfc_target()
        while True:
            numdev = poll(
                self.pdevice, _modulations, len(_modulations), times, delay, target
            )
            if numdev <= 0:
                return
            ptarget = tag_new(self.pdevice, target.nti.nai)
            if not ptarget:
                continue
            ret = Target(ptarget)
            if ret.type == nfc.DESFIRE:
                ret = Desfire(ptarget)
            elif ret.type == nfc.CLASSIC_1K or ret.type == nfc.CLASSIC_4K:
                ret = Mifare(ptarget)
            yield ret
            nfc.freefare_free_tag(ptarget)

    def __del__(self):
        # type: () -> None
        """Terminate comms with reader cleanly."""
        if self.pdevice:
            nfc.nfc_close(self.pdevice)
        nfc.nfc_exit(self.pctx)


class Target(object):
    """Target devices that may enter our field."""

    def __init__(self, target):
        # type: (int) -> None
        """Create target device."""
        self.target = target

    @property
    def uid(self):
        # type: () -> bytes
        """
        UID of the device.

        (can vary in length based on type)
        (do not rely on them being absolutly unique)
        """
        return ctypes.string_at(nfc.freefare_get_tag_uid(self.target))

    @property
    def type(self):
        # type: () -> int
        """Type of this device."""
        return int(nfc.freefare_get_tag_type(self.target))


class Desfire(Target):
    """Specialize for DesFire devices."""

    def auth(self, key, keyno=0):
        # type: (bytes, int) -> bool
        """Authenticate."""
        if desfire_connect(self.target) != 0:
            return False
        if len(key) == 8:
            key = (ctypes.c_ubyte * 8)(*bytearray(key))  # type: ignore
            desfire_key = nfc.mifare_desfire_des_key_new_with_version(key)
        else:
            key = (ctypes.c_ubyte * 16)(*bytearray(key))  # type: ignore
            desfire_key = nfc.mifare_desfire_aes_key_new_with_version(key, 1)
        ret = int(desfire_auth(self.target, keyno, desfire_key))
        nfc.mifare_desfire_key_free(desfire_key)
        return ret == 0


class Mifare(Target):
    """Specialize for Mifare devices."""

    def auth(self, data, sector=1, akey=True):
        # type: (bytes, int, bool) -> bool
        """Authenticate."""
        if classic_connect(self.target) != 0:
            return False
        block = nfc.mifare_classic_sector_last_block(sector)
        auth_tag = nfc.mifare_classic_tag.from_buffer_copy(data)
        if akey:
            ret = int(
                classic_auth(
                    self.target, block, auth_tag.amb[block].mbt.abtKeyA, nfc.MFC_KEY_A
                )
            )
        else:
            ret = int(
                classic_auth(
                    self.target, block, auth_tag.amb[block].mbt.abtKeyB, nfc.MFC_KEY_B
                )
            )
        return ret == 0
