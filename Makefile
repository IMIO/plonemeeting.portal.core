#!/usr/bin/make
#
args = $(filter-out $@,$(MAKECMDGOALS))

all: run

.DEFAULT_GOAL:=help

help:  ## Displays this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n\nTargets:\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

.PHONY: bootstrap
bootstrap:  ## Creates virtualenv and installs requirements.txt
	virtualenv -p python3 .
	make install-requirements

install-requirements:
	bin/python bin/pip install -r requirements.txt

.PHONY: buildout
buildout:  ## Runs bootstrap if needed and builds the buildout
	echo "Starting Buildout on $(shell date)"
	rm -f .installed.cfg
	if ! test -f bin/buildout;then make bootstrap;else make install-requirements;fi
	bin/python bin/buildout
	echo "Finished on $(shell date)"

.PHONY: run
run: buildout  ## Runs buildout if needed and starts instance in foregroud
	bin/python bin/instance fg

.PHONY: cleanall
cleanall:  ## Clears build artefacts and virtualenv
	rm -fr bin include lib local share develop-eggs downloads eggs parts .installed.cfg .git/hooks/pre-commit

.PHONY: test
test:
	if test -z "$(args)" ;then bin/test;else bin/test -t $(args);fi
