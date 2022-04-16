# -*- coding: utf-8 -*-
from plone import api
from plone.memoize import ram
from plone.protect.interfaces import IDisableCSRFProtection
from plone.restapi.interfaces import ISerializeToJsonSummary
from plonemeeting.portal.core import logger
from plonemeeting.portal.core.config import DEMO_INSTITUTION_IDS
from plonemeeting.portal.core.config import LOCATIONS_API_URL
from plonemeeting.portal.core.config import REGION_INS_CODE
from Products.Five.browser import BrowserView
from plonemeeting.portal.core.interfaces import IInstitutionSerializeToJson
from zope.component import queryMultiAdapter
from zope.interface import alsoProvides

import json
import requests


def institutions_cachekey(method, self):
    """
    Institution cache key based on a list of ids and last modification date
    """
    brains = api.content.find(portal_type="Institution",
                              review_state="published",
                              sort_on='getId')
    return [brain.id + "_" + str(brain.modified) for brain in brains]


class HomepageView(BrowserView):
    """Homepage view"""

    @ram.cache(institutions_cachekey)
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


class InstitutionLocationsView(BrowserView):
    """Institution locations view"""

    def __call__(self, *args, **kwargs):
        return self.get_institution_locations()

    def fetch_and_store_locations_from_api(self):
        """
        Fetch all institution locations from remote API and store it locally to avoid
        possible downtime from remote API.
        """
        logger.info("Fetching locations data from remote API...")
        query = {
            "rows": 275,
            "facet": "reg_code",
            "refine.reg_code": REGION_INS_CODE,
        }
        try:
            response = requests.get(
                LOCATIONS_API_URL + "&q=",
                params=query,
            )
            # We disable CSRFProtection as it's not necessary here
            # It is not a form view and we deal with the data internally so it's OK to disable it
            alsoProvides(self.request, IDisableCSRFProtection)
            self.context.api_institution_locations = response.json()
        except requests.exceptions.RequestException as e:
            logger.error("Fetching locations data from remote API has failed! "
                         "Check remote API : " + LOCATIONS_API_URL)
            logger.error(e)

        logger.info("Locations data fetched and stored successfully")

    @ram.cache(institutions_cachekey)
    def get_institution_locations(self):
        """
        Get published institution locations in GeoJSON format
        """
        if not hasattr(self.context, "api_institution_locations"):
            self.fetch_and_store_locations_from_api()

        # Get all published institutions and put them in a dict with title as key
        brains = api.content.find(portal_type="Institution", review_state="published")
        institutions_by_titles = {}
        for brain in brains:
            institution = brain.getObject()
            institutions_by_titles[institution.Title()] = institution
        institution_locations = {}

        # Reconcile api_institution_locations and institutions_by_titles based on
        # institution title. TODO : Use something else to reconcile, e.g. 'INS code' for example
        for record in self.context.api_institution_locations["records"]:
            if record["fields"]["mun_name_fr"] in institutions_by_titles.keys():
                institution = institutions_by_titles[record["fields"]["mun_name_fr"]]
                institution_locations[institution.getId()] = {
                    "id": record["fields"]["mun_name_fr"],
                    "URL": institution.absolute_url(),
                    "data": record
                }

        self.request.response.setHeader("Content-type", "application/json")
        return json.dumps(institution_locations)
