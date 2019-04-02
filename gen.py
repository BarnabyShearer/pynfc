from __future__ import print_function

import os
import ctypes
import sys

from clang.cindex import TypeKind
from ctypeslib.codegen import clangparser, typedesc
from ctypeslib.codegen.codegenerator import Generator


class MyGenerator(Generator):
    def type_name(self, t, generate=True):
        """
        Override POINTER_T; full-disclosure I don't know what it is for, just
        that we get RaspberryPi (arm) support without it.
        """
        if isinstance(t, typedesc.PointerType):
            return "ctypes.POINTER(%s)" % (self.type_name(t.typ, generate))
        else:
            return super(MyGenerator, self).type_name(t, generate)

    def Typedef(self, tp):
        """
        Allow ctypes to handle a few more special types
        """
        sized_types = {
            "size_t": "c_size_t",
            "ssize_t": "c_size_t",
            "wchar_t": "c_wchar",
        }
        name = self.type_name(tp)  # tp.name
        if (isinstance(tp.typ, typedesc.FundamentalType) and
                tp.name in sized_types):
            print(u"%s = ctypes.%s" % \
                (name, sized_types[tp.name]), file=self.stream)
            self.names.add(tp.name)
            return
        return super(MyGenerator, self).Typedef(tp)

def run():
    parser = clangparser.Clang_Parser(('-I/usr/include/clang/5.0/include/',))
    parser.filter_location(
        [
            os.path.abspath('pynfc/nfc.c'),
            os.path.abspath('pynfc/freefare.c'),
            os.path.abspath('pynfc/mifare.c'),
            '/usr/include/freefare.h',
            '/usr/include/nfc/nfc-types.h',
            '/usr/include/nfc/nfc.h',
        ]
    )
    parser.parse(os.path.abspath('pynfc/nfc.c'))
    items = parser.get_result()
    items = [i for i in items if isinstance(i, (typedesc.Function, typedesc.Typedef))]
    with open('pynfc/nfc.py', 'w') as out:
        gen = MyGenerator(
            out,
            searched_dlls=(
                ctypes.CDLL('libfreefare.so'),
            )
        )
        gen.generate_headers(parser)
        gen.generate_code(items)
