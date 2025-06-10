# -*- coding: utf-8 -*-
from plone.app.layout.analytics.view import AnalyticsViewlet
from plone.app.layout.viewlets.content import DocumentBylineViewlet
from plonemeeting.portal.core.content.institution import IInstitution
from plonemeeting.portal.core.utils import is_decisions_manager
from plonemeeting.portal.core.utils import is_publications_manager
from Products.CMFCore.permissions import ManagePortal
from Products.CMFCore.utils import _checkPermission


class PMDocumentBylineViewlet(DocumentBylineViewlet):

    def show(self):
        if not self.anonymous and self.request['PUBLISHED'].__name__ == "view":
            utils_view = self.context.restrictedTraverse("@@utils_view")
            institution = utils_view.get_current_institution()
            return (_checkPermission(ManagePortal, institution) or
                    is_decisions_manager(institution) or
                    is_publications_manager(institution))

    def show_modification_date(self):
        """Show modified no matter it was published, useful for Publication."""
        return True

class PMAnalyticsViewlet(AnalyticsViewlet):

    @property
    def webstats_js(self):
        webstats = super().webstats_js or ""
        utils_view = self.context.restrictedTraverse("@@utils_view")
        if utils_view.is_in_institution():
            # If the context is inside an institution, we want to add the institution's webstats JS
            institution = utils_view.get_current_institution()
            if hasattr(institution, 'webstats_js') and institution.webstats_js:
                webstats += institution.webstats_js
        return webstats
