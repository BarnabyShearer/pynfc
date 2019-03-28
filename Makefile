all: pynfc/nfc.py

pynfc/nfc.py: pynfc/*.c
	clang2py --clang-args='-I/usr/include/clang/5.0/include/' -i -k defst -l libnfc.so -l libfreefare.so  pynfc/nfc.c -o $@

clean:
	-rm pynfc/nfc.py

test: all
	py.test --doctest-modules --ignore=setup.py $(addprefix --ignore=,$(GENPY))
