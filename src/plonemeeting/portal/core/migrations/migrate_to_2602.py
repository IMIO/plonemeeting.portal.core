# -*- coding: utf-8 -*-
from plonemeeting.portal.core.migrations import PlonemeetingMigrator

import logging


logger = logging.getLogger("plonemeeting.portal.core")


class MigrateTo2602(PlonemeetingMigrator):
    def _install_pdfviewer(self):
        """Install imio.pdfviewer, the add-on that provides the PDF viewer.

        The metadata.xml dependency applies only to new installs, so upgraded
        sites install the add-on here.
        """
        if not self.qi.is_product_installed("imio.pdfviewer"):
            self.qi.install_product("imio.pdfviewer")

    def run(self):
        logger.info("Migrating to plonemeeting.portal.core 2602")
        self._install_pdfviewer()
        logger.info("Migration to plonemeeting.portal.core 2602 done.")


def migrate(context):
    """Install imio.pdfviewer."""
    migrator = MigrateTo2602(context)
    migrator.run()
    migrator.finish()
