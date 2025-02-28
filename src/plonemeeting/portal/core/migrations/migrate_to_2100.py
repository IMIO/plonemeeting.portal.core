# -*- coding: utf-8 -*-
from Products.CMFPlone.controlpanel.browser.quickinstaller import InstallerView
from imio.migrator.migrator import Migrator
from plone.base.utils import get_installer

import logging

logger = logging.getLogger("plonemeeting.portal.core")


class MigrateTo2100(Migrator):
    def __init__(self, context, disable_linkintegrity_checks=False):
        super().__init__(context, disable_linkintegrity_checks)
        self.qi: InstallerView = get_installer(self.portal)

    def _uninstall_cookiecuttr(self):
        """Uninstall collective.cookiecuttr if it is installed."""
        if self.qi.is_product_installed('collective.cookiecuttr'):
            self.qi.uninstall_product('collective.cookiecuttr')
            logger.info("Uninstalled collective.cookiecuttr.")

    def run(self):
        logger.info("Migrating to plonemeeting.portal.core 2100")
        self._uninstall_cookiecuttr()
        logger.info("Done.")


def migrate(context):
    """
    This migration function will:
       1) Add new portal_catalog index "has_annexes";
       2) Add new faceted filter "Has annexes?";
       3) Configure new element "Publications".
    """
    migrator = MigrateTo2100(context)
    migrator.run()
    migrator.finish()
