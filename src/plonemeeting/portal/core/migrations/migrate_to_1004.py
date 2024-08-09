# -*- coding: utf-8 -*-

from copy import deepcopy
from imio.migrator.migrator import Migrator
from plone import api
from plonemeeting.portal.core.config import CONFIG_FOLDER_ID
from plonemeeting.portal.core.config import FACETED_DEC_FOLDER_ID
from plonemeeting.portal.core.config import FACETED_DEC_XML_PATH
from plonemeeting.portal.core.utils import set_constrain_types

import logging
import os


logger = logging.getLogger("plonemeeting.portal.core")


class MigrateTo1004(Migrator):

    def _apply_folder_constraints(self):
        """
        Apply contraints on Folders.
        """
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

    def _merge_faceted(self):
        logger.info("Merging faceted folders for every institutions...")
        institutions = [obj for obj in self.portal.objectValues()
                        if obj.portal_type == "Institution"]
        # remove "decisions" folder from every institutions
        for institution in institutions:
            decisions = [obj for obj in institution.objectValues()
                         if obj.portal_type == "Folder" and obj.getId() == "decisions"]
            if decisions:
                api.content.delete(decisions[0])
        # re-apply faceted config
        faceted = self.portal.get(CONFIG_FOLDER_ID).get(FACETED_DEC_FOLDER_ID)
        subtyper = faceted.restrictedTraverse("@@faceted_subtyper")
        subtyper.enable()
        # file is one level up, we are in migrations folder
        faceted_config_path = os.path.join(os.path.dirname(__file__), "..", FACETED_DEC_XML_PATH)
        with open(faceted_config_path, "rb") as faceted_config:
            faceted.unrestrictedTraverse("@@faceted_exportimport").import_xml(
                import_file=faceted_config
            )
        logger.info("Done.")

    def run(self):
        logger.info("Migrating to plonemeeting.portal 1004...")
        self._init_long_representatives_in_charge()
        self._apply_folder_constraints()
        self._merge_faceted()
        self.refreshDatabase(catalogs=False,
                             workflows=True,
                             workflowsToUpdate=["institution_workflow"])


def migrate(context):
    """
    This migration function will:
       1) Initialize the new attribute long_representatives_in_charge;
       2) Apply contraints on Folders;
       3) Merge faceted folder, keep "meetings", delete "decisions";
       4) Update security for elements using institution_workflow.
    """
    migrator = MigrateTo1004(context)
    migrator.run()
    migrator.finish()
