# -*- coding: utf-8 -*-
from Products.CMFPlone.CatalogTool import CatalogTool
from plone import api
from plone.dexterity.browser.view import DefaultView
from plonemeeting.portal.core.browser.nextprevious import NextPrevPortalType
from plonemeeting.portal.core.browser.utils import pretty_file_size, pretty_file_icon
from zope.i18n import translate
from plonemeeting.portal.core import _


class ItemView(DefaultView):
    """
    """
    def get_meeting(self):
        """
        Get the meeting from which the item is part of. Items should always be inside a meeting.
        """
        return self.context.aq_parent

    def get_files_infos(self):
        brains = api.content.find(
            portal_type="File", context=self.context, sort_on="getObjPositionInParent"
        )
        res = []
        for brain in brains:
            file = brain.getObject()
            res.append({
                "file": file,
                "size": pretty_file_size(int(file.get_size())),
                "icon": pretty_file_icon(file.content_type()),
            })
        return res

    def get_next_prev_infos(self):
        """
        Get the previous and next items in the meeting. This is based on Plone's
        implementation of the NextPrev behavior.
        """
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
        return self.context.aq_parent.get_items(objects=False)[-1].number
