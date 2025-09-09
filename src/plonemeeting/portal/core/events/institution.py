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
from plone.protect.utils import addTokenToUrl
from plonemeeting.portal.core import _
from plonemeeting.portal.core import logger
from plonemeeting.portal.core.config import DEC_FOLDER_ID
from plonemeeting.portal.core.config import PUB_FOLDER_ID
from plonemeeting.portal.core.interfaces import IMeetingsFolder
from plonemeeting.portal.core.interfaces import IPublicationsFolder
from plonemeeting.portal.core.utils import create_faceted_folder
from plonemeeting.portal.core.utils import create_templates_folder
from plonemeeting.portal.core.utils import get_decisions_managers_group_id
from plonemeeting.portal.core.utils import get_managers_group_id
from plonemeeting.portal.core.utils import get_members_group_id
from plonemeeting.portal.core.utils import get_publication_creators_group_id
from plonemeeting.portal.core.utils import get_publication_reviewers_group_id
from plonemeeting.portal.core.utils import get_publications_managers_group_id
from plonemeeting.portal.core.utils import set_constrain_types
from zope.globalrequest import getRequest
from zope.i18n import translate
from zope.interface import alsoProvides


def handle_institution_creation(obj, event):
    current_lang = api.portal.get_default_language()[:2]

    # Create decisions faceted folder
    decisions = create_faceted_folder(
        obj,
        translate(_(u"Decisions"),
                  target_language=current_lang),
        id=DEC_FOLDER_ID
    )
    alsoProvides(decisions, IMeetingsFolder)

    IFacetedLayout(decisions).update_layout("faceted-preview-meeting")
    set_constrain_types(decisions, ["Meeting"])

    # Create publications faceted folder
    publications = create_faceted_folder(
        obj,
        translate(_(u"Publications"),
                  target_language=current_lang),
        id=PUB_FOLDER_ID
    )
    alsoProvides(publications, IPublicationsFolder)
    IFacetedLayout(publications).update_layout("faceted-preview-publications")
    set_constrain_types(publications, ["Publication"])

    # Create managers groups and configure local permissions
    institution_title = obj.title

    # Members group
    group_id = get_members_group_id(obj)
    group_title = "{0} Members".format(institution_title)
    api.group.create(groupname=group_id, title=group_title)
    # Managers group
    group_id = get_managers_group_id(obj)
    group_title = "{0} Managers".format(institution_title)
    api.group.create(groupname=group_id, title=group_title)
    obj.manage_setLocalRoles(group_id, ["Editor"])
    # Decisions
    group_id = get_decisions_managers_group_id(obj)
    group_title = "{0} Decisions Managers".format(institution_title)
    api.group.create(groupname=group_id, title=group_title)
    obj.manage_setLocalRoles(group_id, ["Reader"])
    obj.get(DEC_FOLDER_ID).manage_setLocalRoles(group_id, ["Reader", "Contributor", "Editor"])
    # Publications
    # Publications managers
    group_id = get_publications_managers_group_id(obj)
    group_title = "{0} Publications Managers".format(institution_title)
    api.group.create(groupname=group_id, title=group_title)
    obj.manage_setLocalRoles(group_id, ["Reader"])
    obj.get(PUB_FOLDER_ID).manage_setLocalRoles(group_id, ["Reader", "Contributor", "Editor", "Reviewer"])
    obj.reindexObjectSecurity()
    # Publications creators
    # group_id = get_publication_creators_group_id(obj)
    # group_title = "{0} Publications Creators".format(institution_title)
    # api.group.create(groupname=group_id, title=group_title)
    # obj.manage_setLocalRoles(group_id, ["Reader"])
    # obj.get(PUB_FOLDER_ID).manage_setLocalRoles(group_id, ["Reader", "Contributor", "Editor"])
    # obj.reindexObjectSecurity()
    # Publications reviewers
    # group_id = get_publication_reviewers_group_id(obj)
    # group_title = "{0} Publications Reviewers".format(institution_title)
    # api.group.create(groupname=group_id, title=group_title)
    # obj.manage_setLocalRoles(group_id, ["Reader"])
    # obj.get(PUB_FOLDER_ID).manage_setLocalRoles(group_id, ["Reader", "Reviewer", "Editor"])
    # obj.reindexObjectSecurity()
    # Templates
    create_templates_folder(obj)

    request = getRequest()
    if request:  # Request can be `None` during test setup
        request.response.redirect(addTokenToUrl(obj.absolute_url()))


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

    # publish/make private enabled tabs if institution published
    institution_state = api.content.get_state(institution)
    for tab_id in (DEC_FOLDER_ID, PUB_FOLDER_ID):
        if tab_id in institution.enabled_tabs and institution_state != "private":
            new_state_id = "published"
        else:
            new_state_id = "private"
        tab = institution.get(tab_id)
        # tab could be None in MigrateTo2000 because we changed ids
        # this test could be removed when migrated to 2000
        if tab and api.content.get_state(tab) != new_state_id:
            api.content.transition(obj=tab, to_state=new_state_id)


def institution_state_changed(institution, event):
    # bypass if creating institution
    if event.transition is None:
        return

    if event.new_state.id == 'private':
        children = institution.listFolderContents() + institution.decisions.listFolderContents()
    else:
        # only publish enabled tabs
        children = institution.listFolderContents({'id': institution.enabled_tabs})
    for child in children:
        api.content.transition(child, to_state=event.new_state.id)


def handle_institution_deletion(obj, event):
    # Configure manager group & local permissions
    try:
        # Don't use api.group.delete(group_id) because it breaks when trying to delete the entire plone site
        obj.aq_parent.portal_groups.removeGroup(get_members_group_id(obj))
        obj.aq_parent.portal_groups.removeGroup(get_managers_group_id(obj))
        obj.aq_parent.portal_groups.removeGroup(get_decisions_managers_group_id(obj))
        obj.aq_parent.portal_groups.removeGroup(get_publications_managers_group_id(obj))
    except CannotGetPortalError:
        # It's alright, it happens when we try to delete the whole plone site.
        pass
