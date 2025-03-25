build:

clean:
	rm -f *.build *.buildinfo *.changes .coverage *.deb *.dsc *.tar.gz *.tar.xz
	rm -rf *.egg-info/ .tox/ .cache/ .mypy_cache/
	rm -rf docs/build/
	rm -rf .pybuild
	rm -rf htmlcov
	find . -type f -name '*.pyc' -delete
	find . -type d -name '*__pycache__' -delete

test:
	@tox

.PHONY: build clean test
