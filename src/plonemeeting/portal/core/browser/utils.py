# -*- coding: utf-8 -*-
from plone import api
from plone.api.validation import mutually_exclusive_parameters
from plone.app.textfield import RichTextValue
from plone.dexterity.interfaces import IDexterityFTI
from plone.protect.utils import addTokenToUrl
from plonemeeting.portal.core.content.institution import IInstitution
from plonemeeting.portal.core.content.meeting import IMeeting
from plonemeeting.portal.core.interfaces import IMeetingsFolder
from Products.Five.browser import BrowserView
from Products.ZCatalog.interfaces import ICatalogBrain
from zope.component import getUtility
from zope.component import queryUtility
from zope.schema.interfaces import IVocabularyFactory

import os
import plone


class UtilsView(BrowserView):
    """
    """

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
                return self.context.plonemeeting_last_modified.strftime(
                    "%d/%m/%Y %H:%M:%S"
                )

    @mutually_exclusive_parameters("meeting", "UID")
    def get_meeting_url(self, meeting=None, UID=None):
        institution = self.get_current_institution()
        meeting_folder_brains = api.content.find(
            context=institution, object_provides=IMeetingsFolder.__identifier__
        )
        if not meeting_folder_brains:
            return
        meeting_uid = UID or (meeting and meeting.UID())
        if meeting_uid is None:
            url = meeting_folder_brains[0].getURL()
        else:
            url = "{0}#seance={1}".format(meeting_folder_brains[0].getURL(), meeting_uid)
        return url

    @staticmethod
    def get_state(meeting):
        return api.content.get_state(meeting)

    def get_categories_mappings_value(self, key):
        factory = queryUtility(
            IVocabularyFactory, "plonemeeting.portal.vocabularies.global_categories"
        )
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

    def vocab_title(self, context, field):
        """ return title when given the vocabulary and the value key"""
        schema = getUtility(IDexterityFTI, name=context.portal_type).lookupSchema()
        if field not in schema:
            raise ValueError(f"No such field {field} in {context.portal_type} context")

        vocabulary_name = schema.get(field).vocabularyName
        vocabulary_factory = getUtility(IVocabularyFactory, vocabulary_name)
        vocabulary = vocabulary_factory(context)
        return vocabulary.getTerm(getattr(context, field)).title

    def meeting_type(self):
        print(self.get_current_institution())
        return self.vocab_title(self.get_current_institution(), "meeting_type")

    def institution_type(self):
        return self.vocab_title(self.get_current_institution(), "institution_type")


def path_to_dx_default_template():
    dx_path = os.path.dirname(plone.dexterity.browser.__file__)
    return os.path.join(dx_path, "item.pt")
