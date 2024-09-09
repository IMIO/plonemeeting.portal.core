# -*- coding: utf-8 -*-

from plone.app.layout.viewlets.content import DocumentBylineViewlet
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
