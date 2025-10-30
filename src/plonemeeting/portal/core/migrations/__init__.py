from eea.facetednavigation.subtypes.interfaces import IPossibleFacetedNavigable
from imio.migrator.migrator import Migrator
from pathlib import Path
from plone import api
from plone.base.utils import get_installer
from plonemeeting.portal.core.config import CONFIG_FOLDER_ID
from plonemeeting.portal.core.config import FACETED_CONFIGS
from Products.CMFPlone.controlpanel.browser.quickinstaller import InstallerView
from zope.component import getMultiAdapter
from zope.interface import alsoProvides

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
