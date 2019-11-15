# -*- coding: utf-8 -*-

from Products.Five.browser import BrowserView
from plone import api


class UtilsView(BrowserView):
    """
    """

    def get_linked_meeting(self, batch):
        brain = batch[0]
        meeting_UID = brain.linkedMeetingUID
        meeting = api.content.get(UID=meeting_UID)
        return meeting
