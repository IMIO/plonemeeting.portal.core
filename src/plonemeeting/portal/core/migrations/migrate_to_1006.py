# -*- coding: utf-8 -*-

from imio.migrator.migrator import Migrator

import logging


logger = logging.getLogger("plonemeeting.portal.core")


class MigrateTo1006(Migrator):

    def _transform_delib_categories_to_dict(self):
        logger.info("Transforming delib_categories to proper dict...")
        brains = self.catalog(portal_type="Institution")
        for brain in brains:
            institution = brain.getObject()
            cat_dict = {}
            if hasattr(institution, "delib_categories") and institution.delib_categories:
                cat_dict = {}
                for category_id, category_title in institution.delib_categories:
                    cat_dict[category_id] = category_title
            institution.delib_categories = cat_dict

        logger.info("Done.")

    def run(self):
        logger.info("Migrating to plonemeeting.portal.core 1006...")
        self._transform_delib_categories_to_dict()


def migrate(context):
    """
    This migration function will:
       1) migrate delib_categories to proper dict
    """
    migrator = MigrateTo1006(context)
    migrator.run()
    migrator.finish()
