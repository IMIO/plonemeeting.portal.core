# -*- coding: utf-8 -*-

from imio.migrator.migrator import Migrator
from plone import api
from plonemeeting.portal.core.config import CONFIG_FOLDER_ID
from plonemeeting.portal.core.config import FACETED_FOLDER_ID
from plonemeeting.portal.core.config import FACETED_XML_PATH

import logging
import os

logger = logging.getLogger("plonemeeting.portal.core")


class MigrateTo1003(Migrator):

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
        faceted = self.portal.get(CONFIG_FOLDER_ID).get(FACETED_FOLDER_ID)
        subtyper = faceted.restrictedTraverse("@@faceted_subtyper")
        subtyper.enable()
        # file is one level up, we are in migrations folder
        faceted_config_path = os.path.join(os.path.dirname(__file__), "..", FACETED_XML_PATH)
        with open(faceted_config_path, "rb") as faceted_config:
            faceted.unrestrictedTraverse("@@faceted_exportimport").import_xml(
                import_file=faceted_config
            )
        logger.info("Done.")

    def run(self):
        logger.info("Migrating to plonemeeting.portal 1003...")
        self._merge_faceted()


def migrate(context):
    """
    This migration function will:

       1) Merge faceted folders;
    """
    migrator = MigrateTo1003(context)
    migrator.run()
    migrator.finish()
