.PHONY: build check test validate serve clean all help

PYTHON ?= python3
PORT   ?= 8000

help:
	@echo "make build     Build the site into public/"
	@echo "make check     Build and validate the generated output"
	@echo "make test      Run the build toolchain unit tests"
	@echo "make validate  test + check (the full gate; run this before pushing)"
	@echo "make serve     Build, then serve public/ on http://localhost:$(PORT)"
	@echo "make clean     Remove generated output"

build:
	@$(PYTHON) scripts/build.py

check:
	@$(PYTHON) scripts/build.py --check

test:
	@$(PYTHON) -m unittest discover -s tests -q

validate: test check
	@echo "validate: all checks passed"

all: validate

serve: build
	@echo "Serving http://localhost:$(PORT)  (Ctrl-C to stop)"
	@$(PYTHON) -m http.server $(PORT) --directory public

clean:
	@rm -rf public
