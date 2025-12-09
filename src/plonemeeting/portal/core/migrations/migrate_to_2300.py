# -*- coding: utf-8 -*-
from imio.migrator.migrator import Migrator
from plone import api
from plone.base.interfaces import IBundleRegistry
from plone.base.utils import get_installer
from plone.registry.interfaces import IRegistry
from plonemeeting.portal.core.config import DEFAULT_DOCUMENTGENERATOR_TEMPLATES
from plonemeeting.portal.core.config import PUB_FOLDER_ID
from plonemeeting.portal.core.interfaces import IPlonemeetingPortalConfigFolder
from plonemeeting.portal.core.setuphandlers import create_or_update_default_template
from plonemeeting.portal.core.utils import create_templates_folder
from plonemeeting.portal.core.utils import get_managers_group_id
from plonemeeting.portal.core.utils import get_publication_creators_group_id
from plonemeeting.portal.core.utils import get_publication_reviewers_group_id
from plonemeeting.portal.core.utils import get_publications_managers_group_id
from Products.CMFPlone.controlpanel.browser.quickinstaller import InstallerView
from zope.component import getUtility
from zope.interface import alsoProvides

import logging


logger = logging.getLogger("plonemeeting.portal.core")


class MigrateTo2300(Migrator):
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
            api.group.create(groupname=group_id, title=group_title)
            institution.manage_setLocalRoles(group_id, ["Reader"])
            institution.get(PUB_FOLDER_ID).manage_setLocalRoles(group_id, ["Reader", "Contributor", "Editor"])

            group_id = get_publication_reviewers_group_id(institution)
            group_title = "{0} Publications Reviewers".format(institution.title)
            api.group.create(groupname=group_id, title=group_title)
            institution.manage_setLocalRoles(group_id, ["Reader"])
            institution.get(PUB_FOLDER_ID).manage_setLocalRoles(group_id, ["Reader", "Reviewer", "Editor"])

    def run(self):
        logger.info("Migrating to plonemeeting.portal.core 2200")
        self.ps.runImportStepFromProfile("profile-plonemeeting.portal.core:default", "plone.app.registry")
        self.ps.runImportStepFromProfile("profile-plonemeeting.portal.core:default", "typeinfo")
        self.ps.runImportStepFromProfile("profile-plonemeeting.portal.core:default", "workflow")
        self._configure_new_publication_groups()
        logger.info("Migration to plonemeeting.portal.core 2300 done.")


def migrate(context):
    """
    This migration function will:
       1)Configure new publication groups about the new publication workflow state 'proposed'.
    """
    migrator = MigrateTo2300(context)
    migrator.run()
    migrator.finish()
