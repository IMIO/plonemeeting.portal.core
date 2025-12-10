# -*- coding: utf-8 -*-
from plone import api
from plone.base.utils import get_installer
from plonemeeting.portal.core.config import PUB_FOLDER_ID
from plonemeeting.portal.core.migrations import PlonemeetingMigrator
from plonemeeting.portal.core.utils import get_publication_creators_group_id
from plonemeeting.portal.core.utils import get_publication_reviewers_group_id
from plonemeeting.portal.core.utils import get_publications_managers_group_id
from Products.CMFPlone.controlpanel.browser.quickinstaller import InstallerView

import logging


logger = logging.getLogger("plonemeeting.portal.core")


class MigrateTo2300(PlonemeetingMigrator):
    def __init__(self, context, disable_linkintegrity_checks=False):
        super().__init__(context, disable_linkintegrity_checks)
        self.qi: InstallerView = get_installer(self.portal)

    def _configure_new_publication_groups(self):
        # Add new groups for institution publication validators
        institutions = [obj for obj in self.portal.objectValues() if obj.portal_type == "Institution"]

        for institution in institutions:
            group_id = get_publications_managers_group_id(institution)
            institution.get(PUB_FOLDER_ID).manage_setLocalRoles(
                group_id, ["Reader", "Contributor", "Editor", "Reviewer"]
            )

            group_id = get_publication_creators_group_id(institution)
            # Check group exists
            group_title = "{0} Publications Creators".format(institution.title)
            group = api.group.get(groupname=group_id)
            if group is None:
                api.group.create(groupname=group_id,title=group_title)
            institution.manage_setLocalRoles(group_id, ["Reader"])
            institution.get(PUB_FOLDER_ID).manage_setLocalRoles(group_id, ["Reader", "Contributor"])

            group_id = get_publication_reviewers_group_id(institution)
            group_title = "{0} Publications Reviewers".format(institution.title)
            group = api.group.get(groupname=group_id)
            if group is None:
                api.group.create(groupname=group_id,title=group_title)
            institution.manage_setLocalRoles(group_id, ["Reader"])
            institution.get(PUB_FOLDER_ID).manage_setLocalRoles(group_id, ["Reader", "Reviewer"])

    def run(self):
        logger.info("Migrating to plonemeeting.portal.core 2300")
        self._re_apply_faceted_configs()
        self._configure_new_publication_groups()
        self.ps.runImportStepFromProfile("profile-plonemeeting.portal.core:default", "plone.app.registry")
        self.ps.runImportStepFromProfile("profile-plonemeeting.portal.core:default", "typeinfo")
        self.ps.runImportStepFromProfile("profile-plonemeeting.portal.core:default", "workflow")
        self._update_role_mappings(query={"portal_type": "Publication"})
        logger.info("Migration to plonemeeting.portal.core 2300 done.")


def migrate(context):
    """
    This migration function will:
       1) Re-apply faceted configuration.
       2) Configure new publication groups about the new publication workflow state 'proposed'.
    """
    migrator = MigrateTo2300(context)
    migrator.run()
    migrator.finish()
