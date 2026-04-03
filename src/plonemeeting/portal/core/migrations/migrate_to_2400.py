# -*- coding: utf-8 -*-
from plone.base.utils import get_installer
from plonemeeting.portal.core.migrations import PlonemeetingMigrator

import logging


logger = logging.getLogger("plonemeeting.portal.core")

OMNIA_PRODUCTS = [
    "imio.omnia.core",
    "imio.omnia.assistant",
    "imio.omnia.tinymce",
]


class MigrateTo2400(PlonemeetingMigrator):
    def __init__(self, context, disable_linkintegrity_checks=False):
        super().__init__(context, disable_linkintegrity_checks)
        self.qi = get_installer(self.portal)

    def _install_omnia_packages(self):
        for product in OMNIA_PRODUCTS:
            if not self.qi.is_product_installed(product):
                self.qi.install_product(product)
                logger.info(f"Installed {product}.")
            else:
                logger.info(f"{product} already installed, skipping.")

    def run(self):
        logger.info("Migrating to plonemeeting.portal.core 2400")
        self._install_omnia_packages()
        self.ps.runImportStepFromProfile("profile-plonemeeting.portal.core:default", "typeinfo")
        self.ps.runImportStepFromProfile("profile-plonemeeting.portal.core:default", "rolemap")
        logger.info("Migration to plonemeeting.portal.core 2400 done.")


def migrate(context):
    """
    This migration function will:
       1) Install imio.omnia.core, imio.omnia.assistant, imio.omnia.tinymce.
       2) Re-import typeinfo to register the new AI assistant fields on Institution.
       3) Re-import rolemap to grant Anonymous access to the omnia OpenAI proxy.
    """
    migrator = MigrateTo2400(context)
    migrator.run()
    migrator.finish()
