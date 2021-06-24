# -*- coding: utf-8 -*-
import logging
from copy import deepcopy

from imio.migrator.migrator import Migrator

logger = logging.getLogger("plonemeeting.portal.core")


class MigrateTo1004(Migrator):
    def _init_long_representatives_in_charge(self):
        """
        Initialize the new attribute long_representatives_in_charge
        with the value in representatives_in_charge.
        """
        logger.info("Initialize the new attribute long_representatives_in_charge")
        brains = self.catalog(portal_type="Item")
        for brain in brains:
            item = brain.getObject()
            item.long_representatives_in_charge = deepcopy(item.representatives_in_charge)
        logger.info("Done.")

    def run(self):
        logger.info("Migrating to plonemeeting.portal 1004...")
        self._init_long_representatives_in_charge()
        self.refreshDatabase(catalogs=False,
                             workflows=True,
                             workflowsToUpdate=["institution_workflow"])


def migrate(context):
    """
    This migration function will:
       1) Initialize the new attribute long_representatives_in_charge ;
    """
    migrator = MigrateTo1004(context)
    migrator.run()
    migrator.finish()
