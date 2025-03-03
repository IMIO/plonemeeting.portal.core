# -*- coding: utf-8 -*-
import logging

from Products.CMFPlone.controlpanel.browser.quickinstaller import InstallerView
from imio.migrator.migrator import Migrator
from plone.base.interfaces import IBundleRegistry
from plone.base.utils import get_installer
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

logger = logging.getLogger("plonemeeting.portal.core")


class MigrateTo2100(Migrator):
    def __init__(self, context, disable_linkintegrity_checks=False):
        super().__init__(context, disable_linkintegrity_checks)
        self.qi: InstallerView = get_installer(self.portal)

    def _uninstall_unnecessary_packages(self):
        """Uninstall some unnecessary packages if they are installed."""
        if self.qi.is_product_installed('collective.cookiecuttr'):
            self.qi.uninstall_product('collective.cookiecuttr')
            logger.info("Uninstalled collective.cookiecuttr.")

        deleted_packages = [
            "collective.cookiecuttr",
            "eea.jquery",
            "collective.js.jqueryui",
        ]
        packages_to_remove = [
            pkg
            for pkg in self.ps._profile_upgrade_versions.keys()
            if any(dp in pkg for dp in deleted_packages)
        ]
        for pkg in packages_to_remove:
            del self.ps._profile_upgrade_versions[pkg]

        registry = getUtility(IRegistry)
        bundles = registry.collectionOfInterface(
            IBundleRegistry, prefix="plone.bundles", check=False
        )

        for bundle_to_delete in ("cookiecuttr", "cookiecuttr-cookie"):
            if bundle_to_delete in bundles:
                del bundles[bundle_to_delete]

    def run(self):
        logger.info("Migrating to plonemeeting.portal.core 2100")
        self._uninstall_unnecessary_packages()
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
