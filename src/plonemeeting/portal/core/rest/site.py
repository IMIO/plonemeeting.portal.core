# -*- coding: utf-8 -*-
from plone import api
from plone.memoize import ram
from plone.protect.interfaces import IDisableCSRFProtection
from plone.restapi.interfaces import ISerializeToJson
from plonemeeting.portal.core import logger
from plonemeeting.portal.core.cache import published_institutions_modified_cachekey
from plonemeeting.portal.core.config import DEMO_INSTITUTION_IDS
from plonemeeting.portal.core.config import LOCATIONS_API_URL
from plonemeeting.portal.core.config import REGION_INS_CODE
from plonemeeting.portal.core.rest.base import PublicAPIView
from plonemeeting.portal.core.rest.interfaces import IInstitutionSerializeToJson
from Products.Five.browser import BrowserView
from zope.component import getUtility
from zope.component import queryMultiAdapter
from zope.interface import alsoProvides
from zope.schema.interfaces import IVocabularyFactory

import json
import requests


class InstitutionLocationsAPIView(PublicAPIView):
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

    @ram.cache(published_institutions_modified_cachekey)
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
