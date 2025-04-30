# -*- coding: utf-8 -*-
from imio.migrator.migrator import Migrator
from plone import api
from plone.base.interfaces import IBundleRegistry
from plone.base.utils import get_installer
from plone.registry.interfaces import IRegistry
from plonemeeting.portal.core.utils import get_managers_group_id
from plonemeeting.portal.core.utils import get_members_group_id
from Products.CMFPlone.controlpanel.browser.quickinstaller import InstallerView
from zope.component import getUtility

import logging


logger = logging.getLogger("plonemeeting.portal.core")


class MigrateTo2100(Migrator):
    def __init__(self, context, disable_linkintegrity_checks=False):
        super().__init__(context, disable_linkintegrity_checks)
        self.qi: InstallerView = get_installer(self.portal)
        self.portal_groups = api.portal.get_tool("portal_groups")
        self.existing_group_ids = [g.id for g in self.portal_groups.listGroups()]

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

    def _add_institution_members_groups(self):
        """Add new groups for institution members."""
        institutions = [obj for obj in self.portal.objectValues()
                        if obj.portal_type == "Institution"]
        for institution in institutions:
            group_id = get_members_group_id(institution)
            group_title = "{0} Members".format(institution.title)
            api.group.create(groupname=group_id, title=group_title)

            # Grab all groups, then filter by those that start with institution_id
            all_groups = self.portal_groups.listGroups()
            matching_groups = [g for g in all_groups if g.getName().startswith(f"{institution.id}-")]
            # Collect all user IDs from these groups
            users_id = set()
            for group in matching_groups:
                users_id.update([u.id for u in group.getGroupMembers()])

            for user_id in users_id:
                api.group.add_user(
                    groupname=group_id,
                    username=user_id
            )

    def _add_institution_managers_groups(self):
        institutions = [obj for obj in self.portal.objectValues()
                        if obj.portal_type == "Institution"]
        for institution in institutions:
            group_id = get_managers_group_id(institution)
            group_title = "{0} Managers".format(institution.title)
            if group_id not in self.existing_group_ids:
                api.group.create(groupname=group_id, title=group_title)
            institution.manage_setLocalRoles(group_id, ["Editor"])

    def run(self):
        logger.info("Migrating to plonemeeting.portal.core 2100")
        self._uninstall_unnecessary_packages()
        self._add_institution_members_groups()
        self._add_institution_managers_groups()
        self.ps.runImportStepFromProfile(
            "profile-plonemeeting.portal.core:default", "actions"
        )  # re-import actions, to add the institution settings tab in the navbar.
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
