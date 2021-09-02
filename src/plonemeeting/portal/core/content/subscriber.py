# -*- coding: utf-8 -*-

from eea.facetednavigation.layout.interfaces import IFacetedLayout
from plone import api
from plone.api.portal import get_registry_record
from zope.globalrequest import getRequest
from zope.interface import alsoProvides
from zope.i18n import translate

from plonemeeting.portal.core import _, logger
from plonemeeting.portal.core.config import APP_FOLDER_ID
from plonemeeting.portal.core.interfaces import IMeetingsFolder
from plonemeeting.portal.core.utils import create_faceted_folder, set_constrain_types
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
        obj,
        translate(_(u"Meetings"),
                  target_language=current_lang),
        id=APP_FOLDER_ID
    )
    alsoProvides(meetings, IMeetingsFolder)
    IFacetedLayout(meetings).update_layout("faceted-preview-meeting")
    set_constrain_types(meetings, [])

    request = getRequest()
    if request:  # Request can be `None` during test setup
        request.response.redirect(obj.absolute_url())


def handle_institution_modified(institution, event):
    """
    Initializes categories_mappings by trying to match global categories with fetched categories from iA.Delib.
    """
    local_categories = getattr(institution, institution.get_delib_categories_attr_name(), {})
    if local_categories and not institution.categories_mappings:
        logger.info("Initializing default categories mappings by matching with those fetched from iA.Delib.")
        global_categories = [cat for cat in get_registry_record(name="plonemeeting.portal.core.global_categories")]
        categories_mappings = []
        for local_category_id in local_categories.keys():
            if local_category_id in global_categories:
                categories_mappings.append({"local_category_id": local_category_id,
                                            "global_category_id": local_category_id})
        institution.categories_mappings = categories_mappings
        logger.info("{} fetched iA.Delib categories matched.".format(len(categories_mappings)))


def institution_state_changed(obj, event):
    content_filter = {'portal_type': 'Folder'}
    if event.new_state.id == 'private':
        content_filter = {}
    for child in obj.listFolderContents(contentFilter=content_filter):
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
