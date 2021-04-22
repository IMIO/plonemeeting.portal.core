# -*- coding: utf-8 -*-

from eea.facetednavigation.layout.interfaces import IFacetedLayout
from plone import api
from zope.globalrequest import getRequest
from zope.interface import alsoProvides
from zope.i18n import translate

from plonemeeting.portal.core import _
from plonemeeting.portal.core.interfaces import IItemsFolder
from plonemeeting.portal.core.interfaces import IMeetingsFolder
from plonemeeting.portal.core.utils import create_faceted_folder
from plonemeeting.portal.core.utils import format_institution_managers_group_id


def handle_institution_creation(obj, event):
    current_lang = api.portal.get_default_language()[:2]
    institution_title = obj.title

    # Configure manager group & local permissions
    group_id = format_institution_managers_group_id(obj)
    group_title = "{0} Institution Managers".format(institution_title)
    api.group.create(groupname=group_id, title=group_title)
    obj.manage_setLocalRoles(group_id, ["Institution Manager", "Contributor"])

    # Create meetings faceted folder
    meetings = create_faceted_folder(
        obj, translate(_(u"Meetings"), target_language=current_lang)
    )
    alsoProvides(meetings, IMeetingsFolder)
    IFacetedLayout(meetings).update_layout("faceted-preview-meeting")

    # Create items faceted folder
    items = create_faceted_folder(
        obj, translate(_(u"Decisions"), target_language=current_lang)
    )
    alsoProvides(items, IItemsFolder)
    IFacetedLayout(items).update_layout("faceted-preview-meeting-items")

    request = getRequest()
    if request:  # Request can be `None` during test setup
        request.response.redirect(obj.absolute_url())


def institution_state_changed(obj, event):
    for child in obj.listFolderContents():
        api.content.transition(child, to_state=event.new_state.id)


def handle_institution_deletion(obj, event):
    # Configure manager group & local permissions
    group_id = format_institution_managers_group_id(obj)
    # Don't use api.group.delete(group_id) because it breaks when trying to delete the entire plone site
    obj.aq_parent.portal_groups.removeGroup(group_id)


def meeting_state_changed(obj, event):
    items = obj.listFolderContents(contentFilter={"portal_type": "Item"})
    for item in items:
        item.reindexObject(idxs=["linkedMeetingReviewState"])
