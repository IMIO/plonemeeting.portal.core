# -*- coding: utf-8 -*-
from eea.facetednavigation.layout.interfaces import IFacetedLayout
from eea.facetednavigation.subtypes.interfaces import IPossibleFacetedNavigable
from imio.helpers.content import object_values
from imio.migrator.migrator import Migrator
from plone import api
from plone.api.exc import GroupNotFoundError
from plone.app.workflow.remap import remap_workflow
from plone.base.utils import get_installer
from plonemeeting.portal.core import _
from plonemeeting.portal.core.config import CONFIG_FOLDER_ID
from plonemeeting.portal.core.config import DEC_FOLDER_ID
from plonemeeting.portal.core.config import FACETED_DEC_FOLDER_ID
from plonemeeting.portal.core.config import FACETED_DEC_XML_PATH
from plonemeeting.portal.core.config import FACETED_PUB_FOLDER_ID
from plonemeeting.portal.core.config import FACETED_PUB_XML_PATH
from plonemeeting.portal.core.config import PUB_FOLDER_ID
from plonemeeting.portal.core.interfaces import IPublicationsFolder
from plonemeeting.portal.core.utils import create_faceted_folder
from plonemeeting.portal.core.utils import get_decisions_managers_group_id
from plonemeeting.portal.core.utils import get_publications_managers_group_id
from plonemeeting.portal.core.utils import set_constrain_types
from Products.CMFCore.Expression import Expression
from Products.CMFPlone.controlpanel.browser.quickinstaller import InstallerView
from zope.component import getMultiAdapter
from zope.i18n import translate
from zope.interface.declarations import alsoProvides

import json
import logging
import os


BREAK = 999

logger = logging.getLogger("plonemeeting.portal.core")


class MigrateTo2000(Migrator):
    def __init__(self, context, disable_linkintegrity_checks=False):
        super().__init__(context, disable_linkintegrity_checks)
        self.qi: InstallerView = get_installer(self.portal)

    def _fix_missing_fingerpointing_icon(self):
        """ This will make plone icon resolver happy and not dump a lot of log for nothing"""
        portal_actions = self.portal.portal_actions
        if "audit-log" in portal_actions.user:
            portal_actions.user["audit-log"].icon_expr = "string:plone-book"
            portal_actions.user["audit-log"].icon_expr_object = Expression("string:plone-book")

    def _remove_footer_customizations(self):
        """ This has been customized over time and should be removed"""
        pvc = self.portal.portal_view_customizations
        if "zope.interface.interface-footer" in pvc:
            pvc.manage_delObjects(['zope.interface.interface-footer'])

    def _fix_faceted_interfaces(self):
        institutions = [obj for obj in self.portal.objectValues()
                        if obj.portal_type == "Institution"]
        i = 0
        for institution in institutions:
            faceted_folder = getattr(institution, DEC_FOLDER_ID)
            alsoProvides(faceted_folder, IPossibleFacetedNavigable)
            i = i + 1
            if i == BREAK:
                break

    def _re_apply_faceted_config(self):
        """ """
        logger.info("Re-applying faceted config")
        # faceted folder was renamed
        current_lang = api.portal.get_default_language()[:2]
        if hasattr(self.portal.get(CONFIG_FOLDER_ID), 'faceted'):
            api.content.rename(self.portal.get(CONFIG_FOLDER_ID).faceted, FACETED_DEC_FOLDER_ID)
        self.portal.get(CONFIG_FOLDER_ID).get(FACETED_DEC_FOLDER_ID).setTitle(
            translate(_("Faceted decisions"), target_language=current_lang))
        # re-apply faceted config
        faceted = self.portal.get(CONFIG_FOLDER_ID).get(FACETED_DEC_FOLDER_ID)
        alsoProvides(faceted, IPossibleFacetedNavigable)
        subtyper = getMultiAdapter((faceted, self.request), name=u'faceted_subtyper')
        subtyper.enable()
        # file is one level up, we are in migrations folder
        faceted_config_path = os.path.join(os.path.dirname(__file__), "..", FACETED_DEC_XML_PATH)
        with open(faceted_config_path, "rb") as faceted_config:
            faceted.unrestrictedTraverse("@@faceted_exportimport").import_xml(
                import_file=faceted_config
            )
        logger.info("Done.")

    def _uninstall_jqueryUI(self):
        logger.info("Uninstalling collective.js.jqueryui...")
        self.qi.uninstall_product("collective.js.jqueryui")
        logger.info("Done.")

    def _upgrades_packages(self):
        """ """
        logger.info("Upgrading packages...")
        self.qi.upgrade_product("eea.facetednavigation")
        self.qi.upgrade_product("collective.z3cform.datagridfield")
        logger.info("Done.")

    def _rename_seances_to_decisions(self):
        """ """
        logger.info("Renaming \"seances\" to \"decisions\" and moving meetings into it...")
        current_lang = api.portal.get_default_language()[:2]
        institutions = [obj for obj in self.portal.objectValues()
                        if obj.portal_type == "Institution"]
        i = 0
        for institution in institutions:
            # make sure constrain types mode is disabled
            set_constrain_types(institution, [], mode=0)
            # rename to "decisions"
            if hasattr(institution, "seances"):
                api.content.rename(institution.seances, DEC_FOLDER_ID)
            decisions = institution.get(DEC_FOLDER_ID)
            decisions.setTitle(translate(_("Decisions"), target_language=current_lang))
            decisions.reindexObject()
            set_constrain_types(decisions, ["Meeting"])

            # move meetings into new folder "decisions"
            for meeting in object_values(institution, "Meeting"):
                # avoid modified on moved element
                orig_modified = meeting.modified()
                orig_items_modified = {item.UID(): item.modified()
                                       for item in object_values(meeting, "Item")}
                api.content.move(meeting, decisions)
                meeting.setModificationDate(orig_modified)
                meeting.reindexObject(idxs=["modified"], update_metadata=1)
                for item in object_values(meeting, "Item"):
                    item.setModificationDate(orig_items_modified[item.UID()])
                    item.reindexObject(idxs=["modified"], update_metadata=1)
            i = i + 1
            if i == BREAK:
                break

    def _configure_publications(self):
        """ """
        logger.info("Configuring \"Publications\"...")
        # add the "Publication" portal_type
        self.ps.runImportStepFromProfile(
            "profile-plonemeeting.portal.core:default", "typeinfo")
        # remove old related "Institution Manager" role and sharing info
        self.ps.runImportStepFromProfile(
            "profile-plonemeeting.portal.core:default", "sharing")
        self.ps.runImportStepFromProfile(
            "profile-plonemeeting.portal.core:default", "rolemap")
        self.ps.runImportStepFromProfile(
            "profile-plonemeeting.portal.core:default", "workflow")
        self.ps.runImportStepFromProfile(
            "profile-plonemeeting.portal.core:default", "catalog")
        # remove role "Institution Manager"
        self.portal._delRoles(["Institution Manager"])
        # remap existing Folders to new manager_folder_workflow
        # set back old workflow for Folder and remap it as "workflow" import step
        # here above will already associate new manage_folder_workflow with Folder type
        self.wfTool.setChainForPortalTypes(['Folder'], ['simple_publication_workflow'])
        remap_workflow(
            context=self.portal,
            type_ids=['Folder'],
            chain=['manager_folder_workflow'],
            state_map={'private': 'private',
                       'published': 'published'})
        # add document_types and legislative_authorities
        current_dir = os.path.abspath(os.path.dirname(__file__))
        json_path = os.path.join(current_dir, "../profiles/demo/data/data.json")
        with open(json_path) as json_str:
            data = json.load(json_str)
            api.portal.set_registry_record(
                "plonemeeting.portal.core.document_types",
                data["document_types"]
            )
            api.portal.set_registry_record(
                "plonemeeting.portal.core.legislative_authorities",
                data["legislative_authorities"]
            )
        # create faceted config
        config_folder = self.portal.get(CONFIG_FOLDER_ID)
        current_lang = api.portal.get_default_language()[:2]
        if FACETED_PUB_FOLDER_ID not in config_folder:
            faceted = create_faceted_folder(
                config_folder,
                translate(_("Faceted publications"), target_language=current_lang),
                id=FACETED_PUB_FOLDER_ID,
            )
        else:
            faceted = config_folder[FACETED_PUB_FOLDER_ID]
        faceted_config_path = os.path.join(os.path.dirname(__file__), "..", FACETED_PUB_XML_PATH)
        with open(faceted_config_path, "rb") as faceted_config:
            faceted.unrestrictedTraverse("@@faceted_exportimport").import_xml(
                import_file=faceted_config
            )
        # update every institutions to add the "Publications" folder
        institutions = [obj for obj in self.portal.objectValues()
                        if obj.portal_type == "Institution"]
        i = 0
        for institution in institutions:
            # for existing institutions, disable "Publications" for now
            institution.enabled_tabs = [DEC_FOLDER_ID]
            if PUB_FOLDER_ID not in institution:
                publications = create_faceted_folder(
                    institution,
                    translate(_(u"Publications"),
                              target_language=current_lang),
                    id=PUB_FOLDER_ID
                )
                # move "Publications" folder just after "Decisions" folder
                institution.moveObjectToPosition(id=PUB_FOLDER_ID, position=1)
            else:
                publications = institution[PUB_FOLDER_ID]
            alsoProvides(publications, IPublicationsFolder)
            set_constrain_types(publications, ["Publication"])
            IFacetedLayout(publications).update_layout(
                "faceted-preview-publications")
            # create new groups and transfer users
            # Decisions
            group_id = get_decisions_managers_group_id(institution)
            group_title = "{0} Decisions Managers".format(institution.title)
            api.group.create(groupname=group_id, title=group_title)
            institution.manage_setLocalRoles(group_id, ["Reader"])
            # give "Reader/Contributor/Editor" role to the "decisions" folder
            # and any other custom folder except the "publications" folder
            old_group_id = "{0}-institution_managers".format(institution.getId())
            for folder in object_values(institution, ["Folder"]):
                if folder.getId() in (PUB_FOLDER_ID, ):
                    continue
                folder.manage_setLocalRoles(
                    group_id, ["Reader", "Contributor", "Editor"])
                # remove eventual old institution_managers local roles
                folder.manage_delLocalRoles([old_group_id])

            # move users from old institution_managers group to
            # new decisions_managers group
            try:
                for user in api.user.get_users(groupname=old_group_id):
                    api.group.add_user(groupname=group_id, username=user.id)
                    api.group.remove_user(groupname=old_group_id, username=user.id)
            except GroupNotFoundError:
                continue
            # remove institution_managers group local_roles on institution
            institution.manage_delLocalRoles([old_group_id])
            # delete old institution_managers group
            api.group.delete(old_group_id)
            # Publications
            group_id = get_publications_managers_group_id(institution)
            group_title = "{0} Publications Managers".format(institution.title)
            api.group.create(groupname=group_id, title=group_title)
            institution.manage_setLocalRoles(group_id, ["Reader"])
            institution.get(PUB_FOLDER_ID).manage_setLocalRoles(
                group_id, ["Reader", "Contributor", "Editor"])
            institution.reindexObjectSecurity()
            i = i + 1
            if i == BREAK:
                break
        logger.info("Done.")

    def run(self):
        logger.info("Migrating to plonemeeting.portal.core 2000")
        self._rename_seances_to_decisions()
        self._configure_publications()
        self._fix_missing_fingerpointing_icon()
        self._fix_faceted_interfaces()
        self._re_apply_faceted_config()
        self._uninstall_jqueryUI()
        self._remove_footer_customizations()
        self._upgrades_packages()
        self.ps.runImportStepFromProfile(
            "profile-plonemeeting.portal.core:default", "actions"
        )  # re-import actions, needed for the configurable footer
        self.ps.runImportStepFromProfile(
            "profile-plone.staticresources:default", "plone.app.registry"
        )  # Making sure we have the latest icons. Weirdly enough, it's not handled by the Plone upgrade
        logger.info("Done.")


def migrate(context):
    """
    This migration function will:
       1) Add new portal_catalog index "has_annexes";
       2) Add new faceted filter "Has annexes?";
       3) Configure new element "Publications".
    """
    migrator = MigrateTo2000(context)
    migrator.run()
    migrator.finish()
