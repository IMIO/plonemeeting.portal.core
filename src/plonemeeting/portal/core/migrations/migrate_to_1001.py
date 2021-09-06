# -*- coding: utf-8 -*-
from imio.migrator.migrator import Migrator

import logging


logger = logging.getLogger("plonemeeting.portal.core")


class MigrateTo1001(Migrator):
    def _get_sortable_number_from_number(self, number):
        """XXX Taken from Products.PloneMeeting :
           This will transform a displayed item number to a sortable value (integer) :
           - 1 -> 100;
           - 2 --> 200;
           - 2.1 --> 201;
           - 2.9 --> 209;
           - 2.10 --> 210;
           - 2.22 --> 222;
           """
        if "." in number:
            new_integer, new_decimal = number.split(".")
            new_integer = new_integer
            new_decimal = new_decimal.zfill(2)
            real_move_number = int("{0}{1}".format(new_integer, new_decimal))
        else:
            real_move_number = int(number) * 100
        return real_move_number

    def migrate_sortable_number(self):
        logger.info("Setting up sortable_number for every existing item...")
        brains = self.catalog(portal_type="Item")
        for brain in brains:
            item = brain.getObject()
            item.sortable_number = self._get_sortable_number_from_number(item.number)

        logger.info("Cleaning up portal_catalog...")
        self.ps.runImportStepFromProfile(
            "profile-plonemeeting.portal.core:default", "catalog"
        )
        self.reindexIndexes(idxs=["number", "sortable_number"], update_metadata=True)
        self.removeUnusedColumns(columns=["item_number"])
        self.removeUnusedIndexes(indexes=["item_number"])

        logger.info("Done.")

    def run(self):
        logger.info("Migrating to plonemeeting.portal 1001...")
        self.migrate_sortable_number()


def migrate(context):
    """
    This migration function will:

       1) set up the new field "sortable_number" on Items;
    """
    migrator = MigrateTo1001(context)
    migrator.run()
    migrator.finish()
