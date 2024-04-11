# -*- coding: utf-8 -*-
from Products.CMFCore.Expression import Expression
from eea.facetednavigation.subtypes.interfaces import IPossibleFacetedNavigable
from imio.migrator.migrator import Migrator
from zope.component import getMultiAdapter

from zope.interface.declarations import alsoProvides
from plonemeeting.portal.core.config import APP_FOLDER_ID
from plonemeeting.portal.core.config import CONFIG_FOLDER_ID
from plonemeeting.portal.core.config import FACETED_FOLDER_ID
from plonemeeting.portal.core.config import FACETED_XML_PATH

import logging
import os


logger = logging.getLogger("plonemeeting.portal.core")


class MigrateTo2000(Migrator):

    def _fix_missing_fingerpointing_icon(self):
        """ This will make plone icon resolver happy and not dump a lot of log for nothing"""
        portal_actions = self.portal.portal_actions
        if "audit-log" in portal_actions.user:
            portal_actions.user["audit-log"].icon_expr = "string:plone-book"
            portal_actions.user["audit-log"].icon_expr_object = Expression("string:plone-book")

    def _fix_faceted_interfaces(self):
        institutions = [obj for obj in self.portal.objectValues()
                        if obj.portal_type == "Institution"]
        for institution in institutions:
            faceted_folder = getattr(institution, APP_FOLDER_ID)
            alsoProvides(faceted_folder, IPossibleFacetedNavigable)

    def _re_apply_faceted_config(self):
        """ """
        logger.info("Re-applying faceted config to add new filter "
                    "\"Has annexes?\" available to institution managers...")
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


    def run(self):
        logger.info("Migrating to plonemeeting.portal.core 2000...")
        self._fix_missing_fingerpointing_icon()
        self._fix_faceted_interfaces()
        self._re_apply_faceted_config()
        logger.info("Done.")


def migrate(context):
    """
    This migration function will:
       1) Add new portal_catalog index "has_annexes";
       2) Add new faceted filter "Has annexes?";
       3) Rename institution folder containing faceted filters from "meetings" to "seances".
    """
    migrator = MigrateTo2000(context)
    migrator.run()
    migrator.finish()
