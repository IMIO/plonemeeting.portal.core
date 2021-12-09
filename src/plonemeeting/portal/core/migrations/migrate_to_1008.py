# -*- coding: utf-8 -*-

from imio.migrator.migrator import Migrator
from plonemeeting.portal.core.setuphandlers import apply_faceted_config

import logging


logger = logging.getLogger("plonemeeting.portal.core")


class MigrateTo1008(Migrator):

    @staticmethod
    def _reapply_faceted_config():
        logger.info("Apply new faceted configuration ...")
        apply_faceted_config()
        logger.info("Done.")

    def run(self):
        logger.info("Migrating to plonemeeting.portal.core 1007...")
        self._reapply_faceted_config()


def migrate(context):
    """
    This migration function will:
       1) re apply faceted configuration
       2) ...
    """
    migrator = MigrateTo1008(context)
    migrator.run()
    migrator.finish()
