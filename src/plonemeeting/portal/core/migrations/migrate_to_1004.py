# -*- coding: utf-8 -*-
import logging
from copy import deepcopy

from imio.migrator.migrator import Migrator
from plonemeeting.portal.core.utils import set_constrain_types

logger = logging.getLogger("plonemeeting.portal.core")


class MigrateTo1004(Migrator):

    def _apply_folder_constraints(self):
        """
        Apply contraints on Folders.
        """
        logger.info("Reapply typeinfo from plonemeeting.portal.core:default")
        self.ps.runImportStepFromProfile('profile-plonemeeting.portal.core:default', 'content')
        logger.info("Done.")
        logger.info("Apply contraints on Faceted Folders")
        brains = self.catalog(portal_type="Institution")
        for brain in brains:
            institution = brain.getObject()
            for folder_id in ("seances", "decisions"):
                folder = institution.get(folder_id)
                if folder:
                    set_constrain_types(folder, [])
        logger.info("Done.")

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
        self._apply_folder_constraints()


def migrate(context):
    """
    This migration function will:
       1) Initialize the new attribute long_representatives_in_charge ;
       2) Apply contraints on Folders ;
    """
    migrator = MigrateTo1004(context)
    migrator.run()
    migrator.finish()
