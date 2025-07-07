# -*- coding: utf-8 -*-
from plone import api
from plone.api.validation import mutually_exclusive_parameters
from plone.app.textfield import RichTextValue
from plone.protect.utils import addTokenToUrl
from plonemeeting.portal.core import _
from plonemeeting.portal.core.config import MIMETYPE_TO_ICON
from plonemeeting.portal.core.content.institution import IInstitution
from plonemeeting.portal.core.content.meeting import IMeeting
from plonemeeting.portal.core.interfaces import IMeetingsFolder
from plonemeeting.portal.core.interfaces import IPublicationsFolder
from plonemeeting.portal.core.utils import get_term_title
from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from Products.ZCatalog.interfaces import ICatalogBrain
from zope.component import queryUtility
from zope.i18n import translate
from zope.schema.interfaces import IVocabularyFactory

import math
import os
import plone


class UtilsView(BrowserView):
    """ """

    def get_current_institution(self):
        if ICatalogBrain.providedBy(self.context):
            # context could be a brain in a faceted view, so we need to get the real object.
            # Otherwise, api.portal.get_navigation_root returns the PloneSite.
            # Which is not what we want
            obj = self.context.getObject()
            return api.portal.get_navigation_root(obj)
        return self.is_institution() and self.context or api.portal.get_navigation_root(self.context)

    def is_institution(self):
        return IInstitution.providedBy(self.context)

    def is_in_institution(self):
        return IInstitution.providedBy(api.portal.get_navigation_root(self.context))

    def is_meeting(self):
        return IMeeting.providedBy(self.context)

    def get_linked_meeting(self):
        uid = self.request.get("seance[]")
        meeting = None
        if uid:
            meeting = api.content.get(UID=uid)
        return meeting

    def get_plonemeeting_last_modified(self):
        if self.context.plonemeeting_last_modified:
            if not (
                self.context.plonemeeting_last_modified.hour == 0
                and self.context.plonemeeting_last_modified.minute == 0
            ):
                return self.context.plonemeeting_last_modified.strftime("%d/%m/%Y %H:%M:%S")

    @mutually_exclusive_parameters("meeting", "UID")
    def get_meeting_url(self, meeting=None, UID=None):
        institution = self.get_current_institution()
        meeting_folder_brains = api.content.find(context=institution, object_provides=IMeetingsFolder.__identifier__)
        if not meeting_folder_brains:
            return
        meeting_uid = UID or (meeting and meeting.UID())
        if meeting_uid is None:
            url = meeting_folder_brains[0].getURL()
        else:
            url = "{0}#seance={1}".format(meeting_folder_brains[0].getURL(), meeting_uid)
        return url

    def get_publications_url(self):
        institution = self.get_current_institution()
        return api.content.find(context=institution, object_provides=IPublicationsFolder.__identifier__)[0].getURL()

    def get_settings_url(self):
        institution = self.get_current_institution()
        return f"{institution.absolute_url()}/@@manage-settings"

    def show_settings_tab(self):
        portal_membership = getToolByName(self.context, "portal_membership")
        if portal_membership.isAnonymousUser() or not self.is_in_institution():
            return False
        return portal_membership.checkPermission("Modify portal content", self.get_current_institution())

    @staticmethod
    def get_state(obj):
        return api.content.get_state(obj)

    def get_categories_mappings_value(self, key):
        factory = queryUtility(IVocabularyFactory, "plonemeeting.portal.vocabularies.global_categories")
        vocab = factory(self.context)
        return vocab.getTerm(key).title

    def get_project_decision_disclaimer_output(self):
        institution = self.get_current_institution()
        disclaimer = institution.project_decision_disclaimer
        if isinstance(disclaimer, str):
            return disclaimer
        elif isinstance(disclaimer, RichTextValue):
            return disclaimer.output

    def hidden_info_toggle(self):
        form = self.request.form
        if form.get("b_start") != "0":
            # not on the first page
            return True
        if len(form) > 2:
            # filtered results
            return True
        return False

    def protect_url(self, url):
        return addTokenToUrl(url)

    def meeting_type(self):
        return get_term_title(self.get_current_institution(), "meeting_type")

    def institution_type(self):
        return get_term_title(self.get_current_institution(), "institution_type")

    def get_watermark(self, state):
        if state == "in_project":
            return translate(state, domain="plonemeeting.portal.core", context=self.request)
        elif state == "private":
            return _("confidential")
        return ""

    def get_last_item_number(self, meeting):
        return meeting.get_items(objects=False)[-1].number

    def get_files_infos(self):
        brains = api.content.find(portal_type="File", context=self.context, sort_on="getObjPositionInParent")
        res = []
        for brain in brains:
            file = brain.getObject()
            res.append(
                {
                    "file": file,
                    "size": pretty_file_size(int(file.get_size())),
                    "icon_infos": pretty_file_icon(file.content_type()),
                }
            )
        return res


def path_to_dx_default_template():
    dx_path = os.path.dirname(plone.app.dexterity.__file__)
    return os.path.join(dx_path, "browser/item.pt")


def pretty_file_size(size_bytes):
    if size_bytes == 0:
        return "0o"
    size_name = ("o", "Ko", "Mo", "Go", "To", "Po", "Eo", "Zo", "Yo")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"


def pretty_file_icon(mimetype):
    """
    Returns the Bootstrap icon class for a given MIME type.

    :param mimetype: The MIME type to look up.
    :return: A dictionary with 'icon' and 'color' keys.
    """
    # Default icon and color for unknown MIME types
    default_icon = {"icon": "bi bi-file", "color": "bg-grey"}
    return MIMETYPE_TO_ICON.get(mimetype, default_icon)
