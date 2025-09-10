# -*- coding: utf-8 -*-
from collections import OrderedDict
from collective.documentgenerator.config import POD_FORMATS
from collective.documentgenerator.config import VIEWLET_TYPES
from collective.documentgenerator.interfaces import IGenerablePODTemplates
from collective.documentgenerator.viewlets.generationlinks import DocumentGeneratorLinksViewlet
from plone import api
from plone.app.layout.viewlets import ViewletBase
from plone.memoize.view import memoize
from plonemeeting.portal.core.browser.utils import pretty_file_icon
from plonemeeting.portal.core.config import DOCUMENTGENERATOR_GENERABLE_CONTENT_TYPES
from z3c.form.form import EditForm
from zope.component import getAdapter

import mimetypes


class PMDocumentGeneratorLinksViewlet(DocumentGeneratorLinksViewlet):
    """This viewlet displays available documents to generate."""

    def available(self):
        """Overrided to make sure the viewlet is only available for logged-in users."""
        return (
            not api.user.is_anonymous()
            and not isinstance(self.view, EditForm)
            and self.context.portal_type in DOCUMENTGENERATOR_GENERABLE_CONTENT_TYPES
            and bool(self.get_generable_templates())
        )

    def get_generable_templates(self):
        utils_view = self.context.restrictedTraverse("@@utils_view")
        if not utils_view.is_in_institution():
            return super().get_generable_templates()

        generable_templates = []
        portal = api.portal.get()
        institution = api.portal.get_navigation_root(self.context)
        common_templates_folder = portal.unrestrictedTraverse("config/templates")
        institution_templates_folder = getattr(institution, "templates", {})
        for template in common_templates_folder.values():
            if template.getId() in institution.enabled_templates and template.can_be_generated(self.context):
                generable_templates.append(template)
        for template in institution_templates_folder.values():
            if f"{institution.getId()}__{template.getId()}" in institution.enabled_templates and template.can_be_generated(self.context):
                generable_templates.append(template)
        return generable_templates

    # def get_actions(self):
    #     if hasattr(self.view, "_actions"):
    #         return self.view._actions
    #     return {}
    #
    # def get_navigation_links(self):
    #     if hasattr(self.view, "_navigation_links"):
    #         return self.view._navigation_links
    #     return {}

    def pretty_file_icon(self, output_format):
        mimetype = mimetypes.types_map.get(f".{output_format}", "application/octet-stream")
        return pretty_file_icon(mimetype)
