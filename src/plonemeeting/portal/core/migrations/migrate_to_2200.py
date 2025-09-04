# -*- coding: utf-8 -*-
from imio.migrator.migrator import Migrator
from plone import api
from plone.base.interfaces import IBundleRegistry
from plone.base.utils import get_installer
from plone.registry.interfaces import IRegistry
from plonemeeting.portal.core.config import DEFAULT_DOCUMENTGENERATOR_TEMPLATES, PUB_FOLDER_ID
from plonemeeting.portal.core.interfaces import IPlonemeetingPortalConfigFolder
from plonemeeting.portal.core.setuphandlers import create_or_update_default_template
from plonemeeting.portal.core.utils import (
    get_managers_group_id,
    create_templates_folder,
    get_publication_creators_group_id,
    get_publications_managers_group_id,
)
from plonemeeting.portal.core.utils import get_publication_reviewers_group_id
from Products.CMFPlone.controlpanel.browser.quickinstaller import InstallerView
from zope.component import getUtility

import logging

from zope.interface import alsoProvides

logger = logging.getLogger("plonemeeting.portal.core")


class MigrateTo2200(Migrator):
    def __init__(self, context, disable_linkintegrity_checks=False):
        super().__init__(context, disable_linkintegrity_checks)
        self.qi: InstallerView = get_installer(self.portal)

    def _configure_collective_documentgenerator(self):
        """Configure collective.documentgenerator."""
        if not self.qi.is_product_installed("collective.documentgenerator"):
            self.qi.install_product("collective.documentgenerator")
            logger.info("Installed collective.documentgenerator.")

        # First make the global templates folder
        config_folder = self.portal.get("config")
        if "templates" not in config_folder.objectIds():
            create_templates_folder(config_folder)

        # Add default templates if they do not exist
        templates_folder = config_folder.templates
        for key, template in DEFAULT_DOCUMENTGENERATOR_TEMPLATES.items():
            logger.info(f"Adding default template {key} to templates folder")
            create_or_update_default_template(templates_folder, key, **template)

        # Then make the templates folder in each institution
        institutions = [obj for obj in self.portal.objectValues() if obj.portal_type == "Institution"]
        for institution in institutions:
            if "templates" not in institution.objectIds():
                create_templates_folder(institution)
        logger.info("Configured collective.documentgenerator.")

    def _configure_new_publication_workflow_state(self):
        # Add new groups for institution publication validators
        institutions = [obj for obj in self.portal.objectValues() if obj.portal_type == "Institution"]

        for institution in institutions:
            group_id = get_publications_managers_group_id(institution)
            institution.get(PUB_FOLDER_ID).manage_setLocalRoles(
                group_id, ["Reader", "Contributor", "Editor", "Reviewer"]
            )

            group_id = get_publication_creators_group_id(institution)
            group_title = "{0} Publications Creators".format(institution.title)
            api.group.create(groupname=group_id, title=group_title)
            institution.manage_setLocalRoles(group_id, ["Reader"])
            institution.get(PUB_FOLDER_ID).manage_setLocalRoles(group_id, ["Reader", "Contributor", "Editor"])

            group_id = get_publication_reviewers_group_id(institution)
            group_title = "{0} Publications Reviewers".format(institution.title)
            api.group.create(groupname=group_id, title=group_title)
            institution.manage_setLocalRoles(group_id, ["Reader"])
            institution.get(PUB_FOLDER_ID).manage_setLocalRoles(group_id, ["Reader", "Reviewer", "Editor"])

    def _configure_pm_config_folder_view(self):
        """Set an interface on the config folder to have a specific view."""
        config_folder = self.portal.get("config")
        alsoProvides(config_folder, IPlonemeetingPortalConfigFolder)
        logger.info("Configured plonemeeting portal config folder view.")

    def run(self):
        logger.info("Migrating to plonemeeting.portal.core 2200")
        self.ps.runImportStepFromProfile("profile-plonemeeting.portal.core:default", "plone.app.registry")
        self.ps.runImportStepFromProfile("profile-plonemeeting.portal.core:default", "typeinfo")
        self.ps.runImportStepFromProfile("profile-plonemeeting.portal.core:default", "controlpanel")
        self.ps.runImportStepFromProfile("profile-plonemeeting.portal.core:default", "workflow")
        self._configure_collective_documentgenerator()
        self._configure_new_publication_workflow_state()
        self._configure_pm_config_folder_view()
        logger.info("Migration to plonemeeting.portal.core 2200 done.")


def migrate(context):
    """
    This migration function will:
        1) Configure collective.documentgenerator;
        2) Configure plonemeeting portal config folder view.
    """
    migrator = MigrateTo2200(context)
    migrator.run()
    migrator.finish()
