# -*- coding: utf-8 -*-

from imio.migrator.migrator import Migrator
from plonemeeting.portal.core.config import CONFIG_FOLDER_ID
from plonemeeting.portal.core.config import FACETED_DEC_FOLDER_ID
from plonemeeting.portal.core.config import FACETED_DEC_XML_PATH

import logging
import os


logger = logging.getLogger("plonemeeting.portal.core")


class MigrateTo1005(Migrator):

    def _reapply_faceted_config(self):
        logger.info("Re-applying faceted configuuration...")

        faceted = self.portal.get(CONFIG_FOLDER_ID).get(FACETED_DEC_FOLDER_ID)
        # file is one level up, we are in migrations folder
        faceted_config_path = os.path.join(os.path.dirname(__file__), "..", FACETED_DEC_XML_PATH)
        with open(faceted_config_path, "rb") as faceted_config:
            faceted.unrestrictedTraverse("@@faceted_exportimport").import_xml(
                import_file=faceted_config
            )
        logger.info("Done.")

    def run(self):
        logger.info("Migrating to plonemeeting.portal.core 1005...")
        self._reapply_faceted_config()


def migrate(context):
    """
    This migration function will:
       1) Re-apply faceted configuration.
    """
    migrator = MigrateTo1005(context)
    migrator.run()
    migrator.finish()
