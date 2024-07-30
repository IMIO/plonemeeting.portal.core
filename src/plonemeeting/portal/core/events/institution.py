# -*- coding: utf-8 -*-
# from datetime import datetime
# from plone import api
# from plone.registry.interfaces import IRegistry
# from Products.CMFPlone.controlpanel.browser.resourceregistry import OverrideFolderManager
# from Products.CMFPlone.interfaces import IBundleRegistry
# from zope.component import getUtility

from eea.facetednavigation.layout.interfaces import IFacetedLayout
from plone import api
from plone.api.exc import CannotGetPortalError
from plone.api.portal import get_registry_record
from plonemeeting.portal.core import _
from plonemeeting.portal.core import logger
from plonemeeting.portal.core.config import APP_FOLDER_ID
from plonemeeting.portal.core.config import PUB_FOLDER_ID
from plonemeeting.portal.core.interfaces import IMeetingsFolder
from plonemeeting.portal.core.interfaces import IPublicationsFolder
from plonemeeting.portal.core.utils import create_faceted_folder
from plonemeeting.portal.core.utils import format_institution_managers_group_id
from plonemeeting.portal.core.utils import set_constrain_types
from zope.globalrequest import getRequest
from zope.i18n import translate
from zope.interface import alsoProvides


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

    # Create publications faceted folder
    publications = create_faceted_folder(
        obj,
        translate(_(u"Publications"),
                  target_language=current_lang),
        id=PUB_FOLDER_ID
    )
    alsoProvides(publications, IPublicationsFolder)

    # XXX to be changed to "faceted-preview-publication" when available
    IFacetedLayout(publications).update_layout("faceted-preview-items")

    request = getRequest()
    if request:  # Request can be `None` during test setup
        request.response.redirect(obj.absolute_url())


def handle_institution_modified(institution, event):
    """
    Initializes categories_mappings by trying to match global categories with fetched categories from iA.Delib.
    """
    local_categories = getattr(institution, 'delib_categories', {})
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
    try:
        group_id = format_institution_managers_group_id(obj)
        # Don't use api.group.delete(group_id) because it breaks when trying to delete the entire plone site
        obj.aq_parent.portal_groups.removeGroup(group_id)
    except CannotGetPortalError:
        # It's alright, it happens when we try to delete the whole plone site.
        pass


def meeting_state_changed(obj, event):
    items = obj.listFolderContents(contentFilter={"portal_type": "Item"})
    for item in items:
        item.reindexObject(idxs=["linkedMeetingReviewState"])


def update_custom_css(context, event):
    """
    This will update the custom_colors.css in plone_resources directory and will update the bundle
    registry entry when there is an event that add or modify an institution.
    """
    pass
    # TODO
    # First, save the compiled css in the plone_resources directory where static files are stored
    # overrides = OverrideFolderManager(context)
    # bundle_name = "plonemeeting.portal.core-custom"
    # filepath = "static/{0}-compiled.css".format(bundle_name)
    # color_custom_css_view = api.portal.get().unrestrictedTraverse("@@custom_colors.css")
    # compiled_css = color_custom_css_view()

    # overrides.save_file(filepath, compiled_css)

    # Next, update the registry entry for the bundle
    # registry = getUtility(IRegistry)
    # bundles = registry.collectionOfInterface(
    #     IBundleRegistry, prefix="plone.bundles", check=False
    # )
    # bundle = bundles.get(bundle_name)
    # if bundle:
    #     bundle.last_compilation = (
    #         datetime.now()
    #     )  # Important : it's used for cache busting
    #     bundle.csscompilation = "++plone++{}".format(filepath)
