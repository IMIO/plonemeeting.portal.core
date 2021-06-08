# -*- coding: utf-8 -*-

import logging
from imio.migrator.migrator import Migrator
from plone.app.textfield import RichTextValue

logger = logging.getLogger("plonemeeting.portal.core")


class MigrateTo1003(Migrator):
    def fix_formatted_title(self):
        """
        Fix formatted_title on existing items where formatted_title is null
        """
        logger.info("Fixing empty formatted_title to have a value")
        brains = self.catalog(portal_type="Item")
        for brain in brains:
            item = brain.getObject()
            if not item.formatted_title:
                item.formatted_title = RichTextValue(
                    "<p>" + item.title + "</p>", "text/html", "text/html"
                )
        logger.info("Reindexing SearchableText")
        self.reindexIndexes(idxs=["SearchableText"], update_metadata=True)

    def run(self):
        logger.info("Migrating to plonemeeting.portal 1003...")
        self.fix_formatted_title()
        logger.info("Fixed formatted_title")


def migrate(context):
    """
    This migration function will:

       1) Update the registry to add new bundles;
    """
    migrator = MigrateTo1003(context)
    migrator.run()
    migrator.finish()
