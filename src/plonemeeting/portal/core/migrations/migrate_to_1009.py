# -*- coding: utf-8 -*-

from imio.helpers.catalog import addOrUpdateIndexes
from imio.helpers.content import object_ids
from imio.migrator.migrator import Migrator
from plonemeeting.portal.core.config import CONFIG_FOLDER_ID
from plonemeeting.portal.core.config import DEC_FOLDER_ID
from plonemeeting.portal.core.config import FACETED_DEC_FOLDER_ID
from plonemeeting.portal.core.config import FACETED_DEC_XML_PATH

import logging
import os


logger = logging.getLogger("plonemeeting.portal.core")


class MigrateTo1009(Migrator):

    def _add_has_annexes_index(self):
        """ """
        logger.info("Adding new portal_catalog index \"has_annexes\"...")
        addOrUpdateIndexes(
            self.portal,
            indexInfos={
                "has_annexes":
                    ("BooleanIndex", {}),
            }
        )
        logger.info("Done.")

    def _re_apply_faceted_config(self):
        """ """
        logger.info("Re-applying faceted config to add new filter "
                    "\"Has annexes?\" available to institution managers...")
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

    def _rename_app_folder_id(self):
        """config.DEC_FOLDER_ID changed from "seances" to "meetings",
           back to "seances" for URL lisibility."""
        logger.info("Renaming institution faceted folder \"meetings\" to \"seances\"...")
        institutions = [obj for obj in self.portal.objectValues()
                        if obj.portal_type == "Institution"]
        for institution in institutions:
            if "meetings" in object_ids(institution, "Folder"):
                institution.manage_renameObject("meetings", DEC_FOLDER_ID)
        logger.info("Done.")

    def run(self):
        logger.info("Migrating to plonemeeting.portal.core 1009...")
        self._add_has_annexes_index()
        self._re_apply_faceted_config()
        self._rename_app_folder_id()
        logger.info("Done.")


def migrate(context):
    """
    This migration function will:
       1) Add new portal_catalog index "has_annexes";
       2) Add new faceted filter "Has annexes?";
       3) Rename institution folder containing faceted filters from "meetings" to "seances".
    """
    migrator = MigrateTo1009(context)
    migrator.run()
    migrator.finish()
