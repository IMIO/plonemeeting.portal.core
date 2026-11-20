# -*- coding: utf-8 -*-
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

    def run(self):
        logger.info("Migrating to plonemeeting.portal.core 2601")
        self._install_map_wallonia()
        logger.info("Migration to plonemeeting.portal.core 2601 done.")


def migrate(context):
    """Install imio.map.wallonia."""
    migrator = MigrateTo2601(context)
    migrator.run()
    migrator.finish()
