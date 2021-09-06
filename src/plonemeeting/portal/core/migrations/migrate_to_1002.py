# -*- coding: utf-8 -*-

from datetime import datetime
from imio.migrator.migrator import Migrator
from plone.registry.interfaces import IRegistry
from Products.CMFPlone.interfaces import IBundleRegistry
from Products.CMFPlone.interfaces import IResourceRegistry
from Record import Record
from zope.component import getUtility

import logging


logger = logging.getLogger("plonemeeting.portal.core")


class MigrateTo1002(Migrator):
    def add_resources(self):
        registry = getUtility(IRegistry)

        # Create new ressources in the registry
        ressources = registry.collectionOfInterface(
            IResourceRegistry, prefix="plone.resources", check=False
        )

        if "plonemeeting.portal.core" not in ressources:
            ressources["plonemeeting.portal.core"] = Record()
        css_ressource = ressources["plonemeeting.portal.core"]
        css_ressource.css = ["++plone++plonemeeting.portal.core/less/main.less"]

        if "plonemeeting.portal.core-custom" not in ressources:
            ressources["plonemeeting.portal.core-custom"] = Record()
        css_ressource = ressources["plonemeeting.portal.core-custom"]
        css_ressource.css = ["@@custom_colors.css"]

    def add_bundles(self):
        registry = getUtility(IRegistry)

        bundles = registry.collectionOfInterface(
            IBundleRegistry, prefix="plone.bundles", check=False
        )
        # Create new bundles in the registry
        if "plonemeeting.portal.core" not in bundles:
            bundles["plonemeeting.portal.core"] = Record()
        portal_bundle = bundles["plonemeeting.portal.core"]
        portal_bundle.resources = ["plonemeeting.portal.core"]
        portal_bundle.last_compilation = datetime.now()
        portal_bundle.compile = True
        portal_bundle.enabled = True
        portal_bundle.jscompilation = "++plone++plonemeeting.portal.core/js/core.js"
        portal_bundle.csscompilation = (
            "++plone++plonemeeting.portal.core/css/main-compiled.css"
        )

        if "plonemeeting.portal.core-custom" not in bundles:
            bundles["plonemeeting.portal.core-custom"] = Record()
        portal_bundle_custom = bundles["plonemeeting.portal.core-custom"]
        portal_bundle_custom.resources = ["plonemeeting.portal.core-custom"]
        portal_bundle_custom.css = "@@custom_colors.css"
        portal_bundle_custom.compile = True
        portal_bundle_custom.enabled = True
        portal_bundle_custom.last_compilation = datetime.now()

    def run(self):
        logger.info("Migrating to plonemeeting.portal 1002...")
        self.add_resources()
        self.add_bundles()
        logger.info("New resources and bundles successfully added to the registry")


def migrate(context):
    """
    This migration function will:

       1) Update the registry to add new bundles;
    """
    migrator = MigrateTo1002(context)
    migrator.run()
    migrator.finish()
