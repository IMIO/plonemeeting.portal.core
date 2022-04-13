# -*- coding: utf-8 -*-

from imio.migrator.migrator import Migrator

import logging


logger = logging.getLogger("plonemeeting.portal.core")


class MigrateTo1008(Migrator):

    def run(self):
        logger.info("Migrating to plonemeeting.portal.core 1008...")


def migrate(context):
    """
    This migration function will:
       1) migrate delib_categories to proper dict
       2) change TextLine query parameter to datagridfields :
          - additional_meeting_query_string_for_list
          - additional_published_items_query_string
    """
    migrator = MigrateTo1008(context)
    migrator.run()
    migrator.finish()
