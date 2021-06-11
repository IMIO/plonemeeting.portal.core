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
        logger.info("Reindexing SearchableText and pretty_representatives")
        self.reindexIndexes(idxs=["SearchableText", "pretty_representatives"], update_metadata=True)
        logger.info("Done.")

    def run(self):
        logger.info("Migrating to plonemeeting.portal 1003...")
        self._fix_formatted_title()


def migrate(context):
    """
    This migration function will:

       1) Update the registry to add new bundles;
    """
    migrator = MigrateTo1003(context)
    migrator.run()
    migrator.finish()
