
PYUIC=pyuic5
PFLAGS=

all: design/main_design.py

design/%_design.py: design/%.ui
	$(PYUIC) $(PFLAGS) $< -o $@

clean:
	rm design/*.py
