all: pynfc/nfc.py

pynfc/nfc.py: pynfc/nfc.c pynfc/freefare.c pynfc/mifare.c
	./gen.py $+ > $@

clean:
	-rm pynfc/nfc.py

test: all
	py.test --doctest-modules --ignore=setup.py $(addprefix --ignore=,$(GENPY))
