# -*- coding: utf-8 -*-
from Products.CMFPlone.CatalogTool import CatalogTool
from plone import api
from plone.dexterity.browser.view import DefaultView
from plonemeeting.portal.core.browser.nextprevious import NextPrevPortalType
from zope.i18n import translate
from plonemeeting.portal.core import _


class ItemView(DefaultView):
    """
    """

    def get_files(self):
        brains = api.content.find(
            portal_type="File", context=self.context, sort_on="getObjPositionInParent"
        )
        return brains

    def get_watermark(self, state):
        if state == 'in_project':
            return translate(state, domain="plonemeeting.portal.core", context=self.request)
        elif state == 'private':
            return _("confidential")
        return ""

    def get_next_prev_infos(self):
        res = {}
        try:
            nextprevious = NextPrevPortalType(self.context.aq_parent, "Item")
            res.update(
                {"previous_item": nextprevious.getPreviousItem(self.context),
                 "next_item": nextprevious.getNextItem(self.context)}
            )
        except ValueError:
            # If we're serializing an old version that was renamed or moved,
            # then its id might not be found inside the current object's container.
            res.update({"previous_item": {}, "next_item": {}})
        return res

    def get_last_item_number(self):
        catalog = api.portal.get_tool(name="portal_catalog")
        meeting_path = '/'.join(self.context.aq_parent.getPhysicalPath())
        return catalog.searchResults(
            portal_type="Item",
            path={'query': meeting_path, 'depth': 1},
            sort_on = "sortable_number"
        )[-1].number
