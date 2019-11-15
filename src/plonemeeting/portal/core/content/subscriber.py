# -*- coding: utf-8 -*-

from plone import api
from zope.interface import alsoProvides
from zope.i18n import translate

from plonemeeting.portal.core import _
from plonemeeting.portal.core.interfaces import IMeetingsFolder
from plonemeeting.portal.core.utils import create_faceted_folder
from plonemeeting.portal.core.utils import set_constrain_types


def handle_institution_creation(obj, event):
    institution_id = obj.id
    institution_title = obj.title
    group_id = "{0}-institution_managers".format(institution_id)
    group_title = "{0} Institution Managers".format(institution_title.encode("utf-8"))
    api.group.create(groupname=group_id, title=group_title)
    obj.manage_setLocalRoles(group_id, ["Editor", "Reader", "Contributor", "Reviewer"])
    current_lang = api.portal.get_current_language()[:2]
    meetings = create_faceted_folder(
        obj, translate(_(u"Meetings"), target_language=current_lang)
    )
    alsoProvides(meetings, IMeetingsFolder)
    create_faceted_folder(obj, translate(_(u"Items"), target_language=current_lang))
    # Unauthorize Folder creation in Institution now
    set_constrain_types(obj, ["Meeting"])


def meeting_state_changed(obj, event):
    items = obj.listFolderContents(contentFilter={"portal_type": "Item"})
    for item in items:
        item.reindexObject(idxs=["linkedMeetingReviewState"])
