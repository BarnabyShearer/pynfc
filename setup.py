# type:ignore
"""Setup custom build step."""

from setuptools import setup
from setuptools.command.build_py import build_py


class Build(build_py):
    """Custom build_py step."""

    def run(self):
        """Use ctypelib2 to convert to python."""
        from ctypeslib.codegen import clangparser, config, typedesc
        from ctypeslib.codegen.codegenerator import Generator
        from ctypeslib.library import Library

        parser = clangparser.Clang_Parser(())
        parser.parse("pynfc/nfc.c")
        items = parser.get_result()
        items = [
            i for i in items if isinstance(i, (typedesc.Function, typedesc.Typedef))
        ]
        conf = config.CodegenConfig()
        conf.searched_dlls = (
            Library("/usr/lib/x86_64-linux-gnu/libnfc.so", "nm"),
            Library("/usr/lib/x86_64-linux-gnu/libfreefare.so", "nm"),
        )
        with open("pynfc/nfc.py", "w") as out:
            gen = Generator(out, conf)
            gen.generate_headers(parser)
            gen.generate_code(items)

        return build_py.run(self)


setup(cmdclass={"build_py": Build})
