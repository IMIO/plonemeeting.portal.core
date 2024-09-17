# -*- coding: utf-8 -*-

def meeting_state_changed(obj, event):
    items = obj.listFolderContents(contentFilter={"portal_type": "Item"})
    for item in items:
        item.reindexObject(idxs=["linkedMeetingReviewState"])
