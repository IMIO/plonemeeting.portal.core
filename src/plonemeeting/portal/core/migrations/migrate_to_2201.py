# -*- coding: utf-8 -*-
from plonemeeting.portal.core.migrations import PlonemeetingMigrator

import logging


logger = logging.getLogger("plonemeeting.portal.core")


class MigrateTo2201(PlonemeetingMigrator):

    def run(self):
        logger.info("Migrating to plonemeeting.portal.core 2201")
        self._re_apply_faceted_configs()
        logger.info("Migration to plonemeeting.portal.core 2201 done.")


def migrate(context):
    """
    This migration function will:
      1) Re-apply faceted configuration.
    """
    migrator = MigrateTo2201(context)
    migrator.run()
    migrator.finish()
