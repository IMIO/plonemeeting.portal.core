# -*- coding: utf-8 -*-
from plonemeeting.portal.core.content.meeting import Meeting


def meeting_state_changed(obj, event):
    items = obj.listFolderContents(contentFilter={"portal_type": "Item"})
    for item in items:
        item.reindexObject(idxs=["linkedMeetingReviewState"])

def handle_meeting_creation(obj: Meeting, event):
    helper = obj.unrestrictedTraverse("@@utils_view")
    if not helper.is_in_institution():
        return
    institution = helper.get_current_institution(obj)
    obj.custom_info = institution.default_meeting_custom_info
