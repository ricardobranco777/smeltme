FILES=smeltme.py
BIN=$(FILES)

.PHONY: all
all: pylint mypy black

.PHONY: pylint
pylint:
	@pylint --disable=line-too-long $(FILES)

.PHONY: mypy
mypy:
	@for f in $(FILES) ; do mypy $$f ; done

.PHONY: black
black:
	@black --check $(FILES)

.PHONY: install
install:
	install -m 0755 $(BIN) $(HOME)/bin/

.PHONY: uninstall
uninstall:
	cd $(HOME)/bin ; rm -f $(BIN)
