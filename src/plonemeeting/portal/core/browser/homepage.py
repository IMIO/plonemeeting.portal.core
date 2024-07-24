# -*- coding: utf-8 -*-
from plone import api
from plone.memoize import ram
from plone.restapi.interfaces import ISerializeToJson
from plonemeeting.portal.core.cache import published_institutions_modified_cachekey
from plonemeeting.portal.core.config import DEMO_INSTITUTION_IDS
from plonemeeting.portal.core.rest.interfaces import IInstitutionSerializeToJson
from Products.Five.browser import BrowserView
from zope.component import getUtility
from zope.component import queryMultiAdapter
from zope.schema.interfaces import IVocabularyFactory

import json


class HomepageView(BrowserView):
    """Homepage view"""

    @ram.cache(published_institutions_modified_cachekey)
    def get_json_institutions(self):
        """
        Get all institutions from this portal and return a summary in JSON
        """
        brains = api.content.find(portal_type="Institution",
                                  review_state="published",
                                  sort_on='getId')
        institutions = {}
        for brain in brains:
            if brain.id not in DEMO_INSTITUTION_IDS:
                institution = brain.getObject()
                serializer = queryMultiAdapter((institution, self.request), IInstitutionSerializeToJson)
                institutions[brain.id] = serializer(fieldnames=["title", "institution_type"])
        return json.dumps(institutions)

    @ram.cache(published_institutions_modified_cachekey)
    def get_json_institution_type_vocabulary(self):
        """
        Get institution_type vocabulary from this portal and serialize it in JSON
        """
        factory = getUtility(IVocabularyFactory, 'plonemeeting.portal.vocabularies.institution_types')
        vocabulary = factory(self.context)
        serializer = queryMultiAdapter((vocabulary, self.request), ISerializeToJson)
        return json.dumps(serializer("institution_type"))

    def get_faq_items(self):
        """
        Get all FAQ items from this portal.
        A FAQ item is a "Document" portal type stored in the 'faq' folder.
        """
        faq_folder = getattr(self.context, "faq", None)
        if not faq_folder:
            return
        brains = api.content.find(context=faq_folder,
                                  portal_type="Document",
                                  review_state="published",
                                  sort_on="getObjPositionInParent")
        faq_items = []
        for brain in brains:
            faq_item = brain.getObject()
            faq_items.append(
                {"id": faq_item.getId(), "title": faq_item.Title(), "text": faq_item.text.output})
        return faq_items
