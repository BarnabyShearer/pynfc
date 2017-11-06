GENPY=$(subst .c,.py,$(wildcard pynfc/*.c))

all: $(GENPY)

pynfc/%.xml: pynfc/%.c
	gccxml.real $+ -fxml=$@

pynfc/%.py: pynfc/%.xml
	xml2py -k defst -l libnfc.so -l libfreefare.so -v $+ -o $@

clean:
	-rm pynfc/*.xml $(GENPY)

test:
	pytest --pylint --doctest-modules --ignore=setup.py $(addprefix --ignore=,$(GENPY))
