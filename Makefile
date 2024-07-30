#!/usr/bin/make
SHELL:=/bin/bash -O globstar
args = $(filter-out $@,$(MAKECMDGOALS))
py = 3.11
plone = 6.0

all: run

.DEFAULT_GOAL:=help

help:  ## Displays this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n\nTargets:\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

.PHONY: buildout
buildout:  ## Runs bootstrap if needed and builds the buildout and update versions.cfg
	echo "Starting Buildout on $(shell date)"
	rm -f .installed.cfg
	python3 -m venv .
	bin/python bin/pip install -r "https://dist.plone.org/release/$(plone)-latest/requirements.txt"
	# bin/pre-commit install
	# bin/pre-commit autoupdate
	# echo "[versions]" > versions.cfg
	bin/python bin/buildout -c test-$(plone).cfg
	echo "Finished on $(shell date)"

.PHONY: run
run:  ## Runs buildout if needed and starts instance in foregroud
	make buildout
	bin/python bin/instance fg

.PHONY: cleanall
cleanall:  ## Clears build artefacts and virtualenv
	rm -fr bin include lib local share develop-eggs downloads eggs parts .installed.cfg .mr.developer.cfg pyvenv.cfg .git/hooks/pre-commit

.PHONY: test
test:
	bin/pip install -U mockito # for dev ide env
	if test -z "$(args)" ;then bin/test;else bin/test -t $(args);fi

.PHONY: resources
resources:  ## Compile resources
	pnpm run build

.PHONY: resources-install
resources-install:  ## Install resources dependencies
	$(MAKE) resources-clean
	pnpm i

.PHONY: resources-clean
resources-clean:  ## Clean all node_modules
	rm -r **/node_modules || true

.PHONY: resources-watch
resources-watch:  ## Start a Webpack dev servers and watch for resources changes
	pnpm run --parallel watch
