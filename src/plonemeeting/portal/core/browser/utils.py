# -*- coding: utf-8 -*-

from Products.Five.browser import BrowserView
from plone import api
from plone.api.validation import mutually_exclusive_parameters

from plonemeeting.portal.core.interfaces import IMeetingsFolder


class UtilsView(BrowserView):
    """
    """

    def get_linked_meeting(self, batch):
        brain = batch[0]
        meeting_UID = brain.linkedMeetingUID
        meeting = api.content.get(UID=meeting_UID)
        return meeting

    @mutually_exclusive_parameters("meeting", "UID")
    def get_meeting_url(self, meeting=None, UID=None):
        institution = api.portal.get_navigation_root(self.context)
        meeting_folder_brains = api.content.find(
            context=institution, object_provides=IMeetingsFolder.__identifier__
        )
        if not meeting_folder_brains:
            return
        UID = UID or meeting.UID()
        url = "{0}#seance={1}".format(meeting_folder_brains[0].getURL(), UID)
        return url

    def get_state(self, meeting):
        return api.content.get_state(meeting)
