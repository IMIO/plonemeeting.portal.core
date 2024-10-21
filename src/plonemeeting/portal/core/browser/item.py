# -*- coding: utf-8 -*-
from plone import api
from plone.dexterity.browser.view import DefaultView
from plonemeeting.portal.core.browser.nextprevious import NextPrevItemNumber


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
            nextprevious = NextPrevItemNumber(self.context.aq_parent)
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

    def show_project_decision_disclaimer(self):
        """ """
        return api.content.get_state(self.get_meeting()) != "decision"
