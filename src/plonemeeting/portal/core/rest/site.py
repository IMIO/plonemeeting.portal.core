# -*- coding: utf-8 -*-
from datetime import datetime
from datetime import timedelta
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
import os
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

class PrometheusExportView(PublicAPIView):
    """Publications Prometheus exporter"""

    def __call__(self):
        return self.publications_stats()

    def publications_stats(self):
        """
        Get publications stats in Prometheus format
        """
        catalog = api.portal.get_tool(name="portal_catalog")
        publications_published = catalog.unrestrictedSearchResults(portal_type="Publication", review_state="published")
        res = "# TYPE publications_published gauge\n"
        res += "# HELP publications_published Number of publications published\n"
        res += "publications_published " + str(len(publications_published)) + "\n\n"

        publications_planned = catalog.unrestrictedSearchResults(portal_type="Publication", review_state="planned")
        res += "# TYPE publications_planned gauge\n"
        res += "# HELP publications_planned Number of publications planned\n"
        res += "publications_planned " + str(len(publications_planned)) + "\n\n"

        now = datetime.now()
        publications_planned_not_published = catalog.unrestrictedSearchResults(portal_type="Publication", review_state="planned", effective=now - timedelta(minutes=60))
        res += "# TYPE publications_planned_late gauge\n"
        res += "# HELP publications_planned_late Number of publications planned but not published\n"
        res += "publications_planned_late " + str(len(publications_planned_not_published)) + "\n\n"

        publications_expired = catalog.unrestrictedSearchResults(portal_type="Publication", review_state="published", expires=now)
        res += "# TYPE publications_expired gauge\n"
        res += "# HELP publications_expired Number of publications expired\n"
        res += "publications_expired " + str(len(publications_expired)) + "\n\n"

        publications_expired_not_removed = catalog.unrestrictedSearchResults(portal_type="Publication", review_state="published", expires=now - timedelta(minutes=60))
        res += "# TYPE publications_expired_late gauge\n"
        res += "# HELP publications_expired_late Number of publications expired but not removed\n"
        res += "publications_expired_late " + str(len(publications_expired_not_removed)) + "\n\n"

        dangling_publications = publications_planned_not_published + publications_expired_not_removed
        res += "# TYPE dangling_publications gauge\n"
        res += "# HELP dangling_publications Number of dangling publications\n"
        res += "dangling_publications " + str(len(dangling_publications)) + "\n\n"

        possible_cron_paths = ["/data/log/cron.log", "./var/log/cron.log"]
        cron_log_path = None
        for possible_cron_path in possible_cron_paths:
            if os.path.exists(possible_cron_path):
                cron_log_path = possible_cron_path
                break

        if cron_log_path:
            last_cron_run = os.path.getmtime(cron_log_path)
            res += "# TYPE last_cron_run gauge\n"
            res += "# HELP last_cron_run Last cron run\n"
            res += "last_cron_run " + str(last_cron_run) + "\n\n"

            cron_is_not_running = last_cron_run < now.timestamp() - 3600
            res += "# TYPE cron_is_not_running gauge\n"
            res += "# HELP cron_is_not_running Cron is not running\n"
            res += "cron_is_not_running " + str(cron_is_not_running) + "\n\n"

        self.request.response.setHeader("Content-type", "text/plain")
        return res
