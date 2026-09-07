.PHONY: build serve clean
build:
	python3 scripts/build.py
serve: build
	python3 -m http.server 8000 --directory public
clean:
	rm -rf public
