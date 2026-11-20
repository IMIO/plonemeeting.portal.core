# -*- coding: utf-8 -*-
from Acquisition import aq_base
from plonemeeting.portal.core.migrations import PlonemeetingMigrator

import logging


logger = logging.getLogger("plonemeeting.portal.core")


class MigrateTo2601(PlonemeetingMigrator):
    def _install_map_wallonia(self):
        """Install imio.map.wallonia, the add-on that provides the homepage map.

        The metadata.xml dependency applies only to new installs, so upgraded
        sites install the add-on here.
        """
        if not self.qi.is_product_installed("imio.map.wallonia"):
            self.qi.install_product("imio.map.wallonia")

    def _remove_stored_locations(self):
        """Remove the municipality locations stored on the portal.

        The homepage map gets its data from imio.map.wallonia.
        """
        if hasattr(aq_base(self.portal), "api_institution_locations"):
            delattr(self.portal, "api_institution_locations")

    def run(self):
        logger.info("Migrating to plonemeeting.portal.core 2601")
        self._install_map_wallonia()
        self._remove_stored_locations()
        logger.info("Migration to plonemeeting.portal.core 2601 done.")


def migrate(context):
    """Install imio.map.wallonia and remove the stored municipality locations."""
    migrator = MigrateTo2601(context)
    migrator.run()
    migrator.finish()
