#!/usr/bin/make
#
args = $(filter-out $@,$(MAKECMDGOALS))
RESOURCES_PATH = src/plonemeeting/portal/core/browser/resources

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
	bin/pre-commit install

.PHONY: buildout
buildout:  ## Runs bootstrap if needed and builds the buildout and update versions.cfg
	echo "Starting Buildout on $(shell date)"
	rm -f .installed.cfg
	if ! test -f bin/buildout;then make bootstrap;else make install-requirements;fi
	bin/pre-commit autoupdate
	echo "[versions]" > versions.cfg
	bin/python bin/buildout
	echo "Finished on $(shell date)"

.PHONY: run
run:  ## Runs buildout if needed and starts instance in foregroud
	make buildout
	bin/python bin/instance fg

.PHONY: cleanall
cleanall:  ## Clears build artefacts and virtualenv
	rm -fr bin include lib local share develop-eggs downloads eggs parts .installed.cfg .git/hooks/pre-commit

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
	#. ${NVM_DIR}/nvm.sh && nvm install --lts
	$(MAKE) -C $(RESOURCES_PATH) install

.PHONY: resources-watch
resources-watch:  ## Start a Webpack dev server and watch for resources changes
	# You can pass your Plone site path with = --env PLONE_SITE_PATH=/conseil
	# Default Plone site path is "/Plone"
	if ! test -d $(RESOURCES_PATH)/node_modules;then make resources-install;fi
	$(MAKE) -C $(RESOURCES_PATH) watch $(args)
