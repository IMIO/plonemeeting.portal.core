#!/usr/bin/make
#
args = $(filter-out $@,$(MAKECMDGOALS))
RESOURCES_PATH = src/plonemeeting/portal/core/browser/resources
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
	bin/python bin/pip install -r "https://dist.plone.org/release/$(plone)-latest/requirements.txt" pre-commit
	bin/pre-commit install
	bin/pre-commit autoupdate
	echo "[versions]" > versions.cfg
	bin/python bin/buildout -c test_plone$(plone).cfg
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
	if ! test -d $(RESOURCES_PATH)/node_modules;then make resources-install;fi
	. ${NVM_DIR}/nvm.sh && nvm use --lts
	$(MAKE) -C $(RESOURCES_PATH) build

.PHONY: resources-install
resources-install:  ## Install resources dependencies
	. ${NVM_DIR}/nvm.sh && nvm install --lts
	$(MAKE) -C $(RESOURCES_PATH) install

.PHONY: resources-watch
resources-watch:  ## Start a Webpack dev server and watch for resources changes
	# You can pass your Plone site path with = --env PLONE_SITE_PATH=/conseil
	# Default Plone site path is "/Plone"
	if ! test -d $(RESOURCES_PATH)/node_modules;then make resources-install;fi
	$(MAKE) -C $(RESOURCES_PATH) watch $(args)
