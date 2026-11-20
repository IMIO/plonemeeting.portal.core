# -*- coding: utf-8 -*-
from plonemeeting.portal.core.migrations import PlonemeetingMigrator

import logging


logger = logging.getLogger("plonemeeting.portal.core")


class MigrateTo2700(PlonemeetingMigrator):
    def _install_ocr(self):
        """Install imio.omnia.ocr, the add-on that generates the text version of a PDF file.

        The metadata.xml dependency applies only to new installs, so upgraded
        sites install the add-on here.
        """
        if not self.qi.is_product_installed("imio.omnia.ocr"):
            self.qi.install_product("imio.omnia.ocr")

    def _enable_ocr_on_publications(self):
        """Give the imio.omnia.ocr behavior to the Publication type.

        The step does not touch the publications. A script generates the text
        version of the existing publications.
        """
        self.ps.runImportStepFromProfile("profile-plonemeeting.portal.core:default", "typeinfo")

    def run(self):
        logger.info("Migrating to plonemeeting.portal.core 2700")
        self._install_ocr()
        self._enable_ocr_on_publications()
        logger.info("Migration to plonemeeting.portal.core 2700 done.")


def migrate(context):
    """Install imio.omnia.ocr and enable its behavior on publications."""
    migrator = MigrateTo2700(context)
    migrator.run()
    migrator.finish()
