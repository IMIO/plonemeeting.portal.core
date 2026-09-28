# -*- coding: utf-8 -*-
from plone import api
from plonemeeting.portal.core.migrations import PlonemeetingMigrator

import logging


logger = logging.getLogger("plonemeeting.portal.core")


class MigrateTo2600(PlonemeetingMigrator):
    def _install_emailkit(self):
        """Install imio.emailkit and set its primary colour and logo.

        The metadata.xml dependency applies only to new installs, so upgraded
        sites install the add-on here. An import of the registry step resets
        the values that a site changed, so the step sets only these records.
        """
        if not self.qi.is_product_installed("imio.emailkit"):
            self.qi.install_product("imio.emailkit")
        api.portal.set_registry_record("imio.emailkit.theme.primary_color", "#DE007B")
        api.portal.set_registry_record(
            "imio.emailkit.theme.logo_url",
            "https://www.deliberations.be/++plone++plonemeeting.portal.core/assets/logo_raster.png",
        )

    def run(self):
        logger.info("Migrating to plonemeeting.portal.core 2600")
        self._install_emailkit()
        logger.info("Migration to plonemeeting.portal.core 2600 done.")


def migrate(context):
    """Install imio.emailkit and set its primary colour and logo."""
    migrator = MigrateTo2600(context)
    migrator.run()
    migrator.finish()
