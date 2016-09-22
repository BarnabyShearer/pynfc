import os
import queue
import threading
import ctypes
from . import nfc, freefare, mifare

class Timeout(Exception):
    pass

class timeout(object):
    def __init__(self, timeoutlength=1):
        self.timeoutlength = timeoutlength

    def __call__(self, f):
        def wrapped_f(*args, **kwargs):
            q = queue.Queue()
            t = threading.Thread(target=lambda : q.put(f(*args, **kwargs)))
            t.daemon = True
            t.start()
            t.join(self.timeoutlength)
            if t.is_alive():
                res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(t.ident), ctypes.py_object(SystemExit))
                raise Timeout("Timeout", f)
            return q.get()
        return wrapped_f

poll = timeout(None)(nfc.nfc_initiator_poll_target)
get_tags = timeout()(freefare.freefare_get_tags)
desfire_connect = timeout()(freefare.mifare_desfire_connect)
desfire_auth = timeout()(freefare.mifare_desfire_authenticate)
classic_connect = timeout()(freefare.mifare_classic_connect)
classic_auth = timeout()(freefare.mifare_classic_authenticate)

class Nfc(object):

    pctx = None
    pdevice = None

    def __init__(self, device=None, log_level=None):
        if log_level is not None:
            os.environ["LIBNFC_LOG_LEVEL"] = str(log_level)
        if device is not None:
            os.environ["LIBNFC_DEFAULT_DEVICE"] = device
        self.pctx = nfc.nfc_init.argtypes[0]._type_()
        nfc.nfc_init(ctypes.byref(self.pctx)) #Mallocs the ctx
        if not self.pctx:
            raise Exception("Couldn't nfc_init (malloc?)")
        self.pdevice = nfc.nfc_open(self.pctx, None)
        if not self.pdevice:
            raise Exception("Couldn't nfc_open (comms?)")

    def poll(self, modulations=((nfc.NMT_ISO14443A, nfc.NBR_424),), times=0xFF, delay=1):
        _modulations = (nfc.nfc_initiator_poll_target.argtypes[1]._type_ * len(modulations))()
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
            elif ret.type == freefare.CLASSIC_1K or ret.type == freefare.CLASIC_4K:
                ret = Mifare(ptarget)
            yield ret
            freefare.freefare_free_tags(ptarget)

    def __del__(self):
        if self.pdevice:
            nfc.nfc_close(self.pdevice)
        nfc.nfc_exit(self.pctx)

class Target(object):

    def __init__(self, target):
        self.target = target

    @property
    def id(self):
        return freefare.freefare_get_tag_uid(self.target).decode('ascii')

    @property
    def type(self):
        return freefare.freefare_get_tag_type(self.target)

class Desfire(Target):

    def auth(self, key, keyno=0):
        if desfire_connect(self.target) != 0:
            return False
        if len(key) == 8:
            key = (ctypes.c_ubyte * 8)(*bytearray(key))
            desfire_key = freefare.mifare_desfire_des_key_new_with_version(key);
        else:
            key = (ctypes.c_ubyte * 16)(*bytearray(key))
            desfire_key = freefare.mifare_desfire_aes_key_new_with_version(key, 1);
        ret = desfire_auth(self.target, keyno, desfire_key)
        freefare.mifare_desfire_key_free(desfire_key)
        return ret == 0

class Mifare(Target):

    def auth(self, data, sector=1, akey=True):
        if classic_connect(self.target) != 0:
            return False
        block = freefare.mifare_classic_sector_last_block(sector)
        auth_tag = mifare.mifare_classic_tag.from_buffer_copy(data)
        if akey:
            ret = classic_auth(self.target, block, auth_tag.amb[block].mbt.abtKeyA, freefare.MFC_KEY_A)
        else:
            ret = classic_auth(self.target, block, auth_tag.amb[block].mbt.abtKeyB, freefare.MFC_KEY_B)
        return ret == 0
