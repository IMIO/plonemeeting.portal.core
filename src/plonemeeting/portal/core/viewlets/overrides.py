# -*- coding: utf-8 -*-

from plone.app.layout.viewlets.content import DocumentBylineViewlet


class PMDocumentBylineViewlet(DocumentBylineViewlet):

    def show(self):
        return not self.anonymous and self.request['PUBLISHED'].__name__ == "view"

    def show_modification_date(self):
        """Show modified no matter it was published, useful for Publication."""
        return True
