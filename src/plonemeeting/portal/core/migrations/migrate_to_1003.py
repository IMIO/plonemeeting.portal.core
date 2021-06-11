# -*- coding: utf-8 -*-

import logging

from imio.helpers.content import richtextval
from imio.migrator.migrator import Migrator

logger = logging.getLogger("plonemeeting.portal.core")


class MigrateTo1003(Migrator):
    def _fix_formatted_title(self):
        """
        Fix formatted_title on existing items where formatted_title is null
        """
        logger.info("Fixing empty formatted_title to have a value")
        brains = self.catalog(portal_type="Item")
        for brain in brains:
            item = brain.getObject()
            if not item.formatted_title:
                item.formatted_title = richtextval("<p>" + item.title + "</p>")
        logger.info("Done.")

    def _install_plone_restapi(self):
        """
        Install plone.restapi and configure the "plone.restapi: Use REST API"
        to give it to "Member" instead "Anonymous".
        """
        logger.info("Installing and configuring plone.restapi...")
        self.install(["plone.restapi"])
        self.runProfileSteps("plonemeeting.portal.core", steps=["rolemap"])
        logger.info("Done.")

    def run(self):
        logger.info("Migrating to plonemeeting.portal 1003...")

        self._fix_formatted_title()
        self.reindexIndexes(idxs=["SearchableText", "pretty_representatives"], update_metadata=True)
        self._install_plone_restapi()


def migrate(context):
    """
    This migration function will:

       1) Update the registry to add new bundles;
       2) Reindex indexes "SearchableText" (related to "_fix_formatted_title" step)
          and "pretty_representatives" now that indexed order was fixed;
       3) Install plone.restapi and configure API access permission.
    """
    migrator = MigrateTo1003(context)
    migrator.run()
    migrator.finish()
