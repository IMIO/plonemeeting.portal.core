# -*- coding: utf-8 -*-

from plone import api
from plone.dexterity.browser.view import DefaultView


class ItemView(DefaultView):
    """
    """

    def get_files(self):
        brains = api.content.find(
            portal_type="File", context=self.context, sort_on="getObjPositionInParent"
        )
        return brains

    def next_item(self):
        return ""

    def previous_item(self):
        return ""
