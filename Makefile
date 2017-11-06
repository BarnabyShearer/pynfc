GENPY=$(subst .c,.py,$(wildcard pynfc/*.c))

all: $(GENPY)

pynfc/%.xml: pynfc/%.c
	$(shell which gccxml.real gccxml | head -n1) $+ -fxml=$@

pynfc/%.py: pynfc/%.xml
	xml2py -k defst -l libnfc.so -l libfreefare.so -v $+ -o $@

clean:
	-rm pynfc/*.xml $(GENPY)

test: all
	py.test --pylint --doctest-modules --ignore=setup.py $(addprefix --ignore=,$(GENPY))
