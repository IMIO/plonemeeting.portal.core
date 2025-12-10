from imio.helpers.workflow import update_role_mappings_for
from imio.migrator.migrator import Migrator
from pathlib import Path
from plone import api
from plone.base.utils import get_installer
from plonemeeting.portal.core.config import CONFIG_FOLDER_ID
from plonemeeting.portal.core.config import FACETED_CONFIGS
from Products.CMFPlone.controlpanel.browser.quickinstaller import InstallerView
from Products.ZCatalog.ProgressHandler import ZLogHandler

import logging


logger = logging.getLogger("plonemeeting.portal.core")


class PlonemeetingMigrator(Migrator):
    def __init__(self, context, disable_linkintegrity_checks=False):
        super().__init__(context, disable_linkintegrity_checks)
        self.qi: InstallerView = get_installer(self.portal)
        self.current_lang = api.portal.get_default_language()[:2]

    def _re_apply_faceted_configs(self):
        """ """
        logger.info("Re-applying faceted configs")
        for faceted_config in FACETED_CONFIGS:
            logger.info(f"Re-applying faceted config for {faceted_config.folder_id}")
            faceted = self.portal.get(CONFIG_FOLDER_ID).get(faceted_config.folder_id)
            # file is one level up, we are in migrations folder
            faceted_config_path = Path(__file__).parent.parent / faceted_config.xml_path
            with open(faceted_config_path, "rb") as faceted_config:
                faceted.unrestrictedTraverse("@@faceted_exportimport").import_xml(
                    import_file=faceted_config
                )
        logger.info("Done.")



    def _update_role_mappings(self, query=None):
        """Update role mappings on objects matching the given catalog query."""
        if query is None:
            query = {}

        logger.info("Updating role mappings with query: %r", query)
        brains = self.catalog(**query)
        total = len(brains)
        logger.info("Found %d objects to update role mappings for", total)

        if not total:
            logger.info("No objects found, nothing to do.")
            return

        pghandler = ZLogHandler(1000)
        pghandler.init("Updating role mappings", total)

        updated = 0
        for idx, brain in enumerate(brains, start=1):
            pghandler.report(idx)

            try:
                obj = brain.getObject()
            except Exception:
                logger.exception(
                    "Could not get object for brain at path %s",
                    getattr(brain, "getPath", lambda: "N/A")(),
                )
                continue

            try:
                update_role_mappings_for(obj)
                updated += 1
            except Exception:
                logger.exception(
                    "Error updating role mappings for %s",
                    getattr(obj, "absolute_url", lambda: brain.getPath())(),
                )
                continue

        pghandler.finish()
        logger.info(
            "Done updating role mappings. Updated %d objects out of %d.",
            updated,
            total,
        )
