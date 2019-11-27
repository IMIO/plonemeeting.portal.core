# -*- coding: utf-8 -*-

from Products.CMFPlone.interfaces.constrains import ISelectableConstrainTypes
from plone import api
from plone.portlets.interfaces import IPortletAssignmentMapping
from plone.portlets.interfaces import IPortletManager
from zope.component import getMultiAdapter
from zope.component import getUtility

from plonemeeting.portal.core.config import CONTENTS_TO_CLEAN
from plonemeeting.portal.core.config import PLONEMEETING_API_MEETINGS_VIEW
from plonemeeting.portal.core.config import PLONEMEETING_API_MEETING_ITEMS_VIEW


def get_api_url_for_meetings(institution, meeting_UID=None):
    if not institution.plonemeeting_url or not institution.meeting_config_id:
        return
    url = "{0}/{1}?getConfigId={2}".format(
        institution.plonemeeting_url.rstrip("/"),
        PLONEMEETING_API_MEETINGS_VIEW,
        institution.meeting_config_id,
    )
    if meeting_UID:
        url = "{0}&UID={1}&fullobjects=True".format(url, meeting_UID)
    else:
        url = "{0}{1}".format(url, institution.additional_meeting_query_string_for_list)
    return url


def get_api_url_for_meeting_items(institution, meeting_UID):
    if not institution.plonemeeting_url or not institution.meeting_config_id:
        return
    url = "{0}/{1}?getConfigId={2}&linkedMeetingUID={3}&fullobjects=True{4}".format(
        institution.plonemeeting_url.rstrip("/"),
        PLONEMEETING_API_MEETING_ITEMS_VIEW,
        institution.meeting_config_id,
        meeting_UID,
        institution.additional_published_items_query_string,
    )
    return url


def create_faceted_folder(container, title, id=None):
    if id:
        folder = api.content.create(
            type="Folder", title=title, container=container, id=id
        )
    else:
        folder = api.content.create(type="Folder", title=title, container=container)
    api.content.transition(folder, to_state="published")
    subtyper = folder.restrictedTraverse("@@faceted_subtyper")
    subtyper.enable()
    set_constrain_types(folder, [])
    return folder


def set_constrain_types(obj, list_contraint):
    behavior = ISelectableConstrainTypes(obj)
    behavior.setConstrainTypesMode(1)
    behavior.setImmediatelyAddableTypes(list_contraint)
    behavior.setLocallyAllowedTypes(list_contraint)


def cleanup_contents():
    portal = api.portal.get()
    for content_id in CONTENTS_TO_CLEAN:
        content = getattr(portal, content_id, None)
        if content:
            api.content.delete(content)


def remove_left_portlets():
    remove_portlets("plone.leftcolumn")


def remove_right_portlets():
    remove_portlets("plone.rightcolumn")


def remove_portlets(column):
    portal = api.portal.get()
    manager = getUtility(IPortletManager, name=column, context=portal)
    assignments = getMultiAdapter((portal, manager), IPortletAssignmentMapping)
    for portlet in assignments:
        del assignments[portlet]


def get_global_category(institution, item_local_category):
    global_category = ""
    if not institution.categories_mappings:
        return item_local_category
    for mapping in institution.categories_mappings:
        if mapping["local_category_id"] == item_local_category:
            return mapping["global_category_id"]
    if not global_category:
        return item_local_category
