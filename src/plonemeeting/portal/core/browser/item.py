# -*- coding: utf-8 -*-
from Products.CMFPlone.CatalogTool import CatalogTool
from plone import api
from plone.dexterity.browser.view import DefaultView
from plone.memoize import ram
from plonemeeting.portal.core.browser.nextprevious import NextPrevPortalType
from plonemeeting.portal.core.browser.utils import pretty_file_size, pretty_file_icon
from plonemeeting.portal.core.cache import item_meeting_modified_cachekey
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

    # @ram.cache(item_meeting_modified_cachekey)
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

    # @ram.cache(item_meeting_modified_cachekey)
    def get_last_item_number(self):
        return self.get_meeting().get_items(objects=False)[-1].number
