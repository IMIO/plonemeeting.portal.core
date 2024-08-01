# -*- coding: utf-8 -*-
from eea.facetednavigation.layout.interfaces import IFacetedLayout
from eea.facetednavigation.subtypes.interfaces import IPossibleFacetedNavigable
from imio.migrator.migrator import Migrator
from plone import api
from plone.base.utils import get_installer
from plonemeeting.portal.core import _
from plonemeeting.portal.core.config import APP_FOLDER_ID
from plonemeeting.portal.core.config import CONFIG_FOLDER_ID
from plonemeeting.portal.core.config import FACETED_FOLDER_ID
from plonemeeting.portal.core.config import FACETED_PUB_FOLDER_ID
from plonemeeting.portal.core.config import FACETED_PUB_XML_PATH
from plonemeeting.portal.core.config import FACETED_XML_PATH
from plonemeeting.portal.core.config import PUB_FOLDER_ID
from plonemeeting.portal.core.interfaces import IPublicationsFolder
from plonemeeting.portal.core.utils import create_faceted_folder
from plonemeeting.portal.core.utils import set_constrain_types
from Products.CMFCore.Expression import Expression
from Products.CMFPlone.controlpanel.browser.quickinstaller import InstallerView
from zope.component import getMultiAdapter
from zope.i18n import translate
from zope.interface.declarations import alsoProvides

import json
import logging
import os


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
        for institution in institutions:
            faceted_folder = getattr(institution, APP_FOLDER_ID)
            alsoProvides(faceted_folder, IPossibleFacetedNavigable)

    def _re_apply_faceted_config(self):
        """ """
        logger.info("Re-applying faceted config")
        # re-apply faceted config
        faceted = self.portal.get(CONFIG_FOLDER_ID).get(FACETED_FOLDER_ID)
        alsoProvides(faceted, IPossibleFacetedNavigable)
        subtyper = getMultiAdapter((faceted, self.request), name=u'faceted_subtyper')
        subtyper.enable()
        # file is one level up, we are in migrations folder
        faceted_config_path = os.path.join(os.path.dirname(__file__), "..", FACETED_XML_PATH)
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
        self.qi.upgrade_product("collective.cookiecuttr")
        logger.info("Done.")

    def _configure_publications(self):
        """ """
        logger.info("Configuring \"Publications\"...")
        # add the "Publication" portal_type
        self.ps.runImportStepFromProfile(
            "profile-plonemeeting.portal.core:default", "typeinfo")
        self.ps.runImportStepFromProfile(
            "profile-plonemeeting.portal.core:default", "rolemap")
        # add the "get_document_type" and "get_legislative_authority" indexes
        self.catalog.addIndex(
            "get_document_type",
            "FieldIndex",
            {"indexed_attrs": ["document_type"]})
        self.catalog.addIndex(
            "get_legislative_authority",
            "FieldIndex",
            {"indexed_attrs": ["legislative_authority"]})
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
        faceted = create_faceted_folder(
            config_folder,
            translate(_(FACETED_PUB_FOLDER_ID.capitalize()), target_language=current_lang),
            id=FACETED_PUB_FOLDER_ID,
        )
        faceted_config_path = os.path.join(os.path.dirname(__file__), "..", FACETED_PUB_XML_PATH)
        with open(faceted_config_path, "rb") as faceted_config:
            faceted.unrestrictedTraverse("@@faceted_exportimport").import_xml(
                import_file=faceted_config
            )
        # update every institutions to add the "Publications" folder
        institutions = [obj for obj in self.portal.objectValues()
                        if obj.portal_type == "Institution"]
        for institution in institutions:
            # make sure constrain types mode is disabled
            set_constrain_types(institution, [], mode=0)
            publications = create_faceted_folder(
                institution,
                translate(_(u"Publications"),
                          target_language=current_lang),
                id=PUB_FOLDER_ID
            )
            alsoProvides(publications, IPublicationsFolder)
            set_constrain_types(publications, ["Publication"])

        # XXX to be changed to "faceted-preview-publication" when available
        IFacetedLayout(publications).update_layout("faceted-preview-items")
        logger.info("Done.")

    def run(self):
        logger.info("Migrating to plonemeeting.portal.core 2000")
        self._fix_missing_fingerpointing_icon()
        self._fix_faceted_interfaces()
        self._re_apply_faceted_config()
        self._uninstall_jqueryUI()
        self._remove_footer_customizations()
        self._upgrades_packages()
        self.ps.runImportStepFromProfile(
            "profile-plonemeeting.portal.core:default", "actions"
        )  # re-import actions, needed for the configurable footer
        self._configure_publications()
        logger.info("Done.")


def migrate(context):
    """
    This migration function will:
       1) Add new portal_catalog index "has_annexes";
       2) Add new faceted filter "Has annexes?";
       3) Rename institution folder containing faceted filters from "meetings" to "seances";
       4) Configure new element "Publications".
    """
    migrator = MigrateTo2000(context)
    migrator.run()
    migrator.finish()
