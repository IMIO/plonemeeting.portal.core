# -*- coding: utf-8 -*-
import logging
import os

from imio.migrator.migrator import Migrator
from plonemeeting.portal.core.config import CONFIG_FOLDER_ID, FACETED_PUB_FOLDER_ID, FACETED_PUB_XML_PATH

logger = logging.getLogger("plonemeeting.portal.core")


class MigrateTo2201(Migrator):

    def _reapply_publications_faceted_config(self):
        logger.info("Re-applying faceted configuration...")

        faceted = self.portal.get(CONFIG_FOLDER_ID).get(FACETED_PUB_FOLDER_ID)
        faceted_config_path = os.path.join(os.path.dirname(__file__), "..", FACETED_PUB_XML_PATH)
        with open(faceted_config_path, "rb") as faceted_config:
            faceted.unrestrictedTraverse("@@faceted_exportimport").import_xml(
                import_file=faceted_config
            )
        logger.info("Done.")

    def run(self):
        logger.info("Migrating to plonemeeting.portal.core 2201")
        self._reapply_publications_faceted_config()
        logger.info("Migration to plonemeeting.portal.core 2201 done.")


def migrate(context):
    """
    This migration function will:
    """
    migrator = MigrateTo2201(context)
    migrator.run()
    migrator.finish()
