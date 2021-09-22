Compiling JS/CSS bundle
------------------------

Prerequisite
************

NodeJS > v12 must be installed.

You can check if it's installed and if you have the correct version with::

    $ node -v

If it's not installed or if you have the wrong version, you can install it with the package manager
of your choice. See here : https://nodejs.org/en/download/package-manager/

If you need multiple node versions on your system, nvm is recommended :
https://github.com/nvm-sh/nvm


Fresh install :

>>> curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.38.0/install.sh | bash
>>> make resources


Developing
**********

Start Plone in foreground::

    $ ./bin/instance fg

Start a Webpack dev server and make it watch for resources changes

You can pass your Plone site path by adding `--env PLONE_SITE_PATH=/conseil`

Default Plone site path is "/Plone"::

    $ make resources-watch


Access your Plone site via http://localhost:3000

(Don't go to http://localhost:8080 as you won't have live-reload and you won't see your changes)


**NOTE: DON'T EVER EDIT OR ADD FILES IN `browser/static`**.

The working directory for bundle development is now `browser/resources`

While the Webpack dev server is running, you can edit files there and see the
changes in real-time in the browser. If you add files in `browser/static` it will not
persist at the next production build.


Production
**********

At the project root::

    $ make resource

This will compile the bundle for production use.

It will populate the `browser/static` folder that Plone will serve.

It will also take care of updating the `last_compilation` in the `registry.xml` file
