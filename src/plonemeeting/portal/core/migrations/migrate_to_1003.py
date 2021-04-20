# -*- coding: utf-8 -*-
from imio.migrator.migrator import Migrator
from plonemeeting.portal.core.config import DEFAULT_CATEGORY_IA_DELIB_FIELD

import logging

logger = logging.getLogger("plonemeeting.portal.core")


class MigrateTo1003(Migrator):
    def run(self):
        logger.info("Migrating to plonemeeting.portal 1003...")
        logger.info("Initialize delib_catogory_field field on all Institution...")

        for brain in self.catalog(portal_type="Institution"):
            institution = brain.getObject()
            institution.delib_catogory_field = DEFAULT_CATEGORY_IA_DELIB_FIELD

        logger.info("Done.")


def migrate(context):
    """
    This migration function will:

       1) Update the registry to add new bundles;
    """
    migrator = MigrateTo1003(context)
    migrator.run()
    migrator.finish()
