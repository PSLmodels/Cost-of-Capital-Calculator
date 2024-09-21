# GNU Makefile that documents and automates common development operations
#              using the GNU make tool (version >= 3.81)
# Development is typically conducted on Linux or Max OS X (with the Xcode
#              command-line tools installed), so this Makefile is designed
#              to work in that environment (and not on Windows).
# USAGE: Cost-of-Capital-Calculator$ make [TARGET]

.PHONY=help
help:
	@echo "USAGE: make [TARGET]"
	@echo "TARGETS:"
	@echo "help       : show help message"
	@echo "clean      : remove .pyc files and local ccc package"
	@echo "package    : build and install local package"
	@echo "pytest     : generate report for and cleanup after"
	@echo "             pytest -W ignore -n4 -m ''"
	@echo "cstest     : generate coding-style errors using the"
	@echo "             pycodestyle (nee pep8) tool"
	@echo "coverage   : generate test coverage report"
	@echo "git-sync   : synchronize local, origin, and upstream Git repos"
	@echo "git-pr N=n : create local pr-n branch containing upstream PR"

.PHONY=clean
clean:
	@find . -name *pyc -exec rm {} \;
	@find . -name *cache -maxdepth 1 -exec rm -r {} \;
	@conda uninstall ccc --yes --quiet 2>&1 > /dev/null

.PHONY=package
package:
	@pbrelease Cost-of-Capital-Calculator ccc 0.0.0 --local

.PHONY=pytest
pytest:
	@cd ccc ; pytest -W ignore -n4

CCC_JSON_FILES := $(shell ls -l ./ccc/*json | awk '{print $$9}')

.PHONY=cstest
cstest:
	-pycodestyle ccc
	-pycodestyle --ignore=E501,E121 $(CCC_JSON_FILES)

define coverage-cleanup
rm -f .coverage htmlcov/*
endef

COVMARK = ""

OS := $(shell uname -s)

.PHONY=coverage
coverage:
	@$(coverage-cleanup)
	@coverage run -m pytest -v -m $(COVMARK) > /dev/null
	@coverage html --ignore-errors
ifeq ($(OS), Darwin) # on Mac OS X
	@open htmlcov/index.html
else
	@echo "Open htmlcov/index.html in browser to view report"
endif
	@$(pytest-cleanup)

.PHONY=git-sync
git-sync:
	@./gitsync

.PHONY=git-pr
git-pr:
	@./gitpr $(N)

.PHONY=build-docs
build-docs:
	@cd ./docs ; python make_params.py; jb build ./book

format:
	black . -l 79
	linecheck . --fix

pip-package:
	pip install wheel
	pip install setuptools
	python setup.py sdist bdist_wheel