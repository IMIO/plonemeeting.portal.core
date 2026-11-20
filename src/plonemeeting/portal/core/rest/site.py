# -*- coding: utf-8 -*-
from datetime import datetime
from datetime import timedelta
from plone import api
from plone.restapi.interfaces import ISerializeToJson
from plonemeeting.portal.core.config import DEMO_INSTITUTION_IDS
from plonemeeting.portal.core.rest.base import PublicAPIView
from plonemeeting.portal.core.rest.interfaces import IInstitutionSerializeToJson
from Products.Five.browser import BrowserView
from zope.component import getUtility
from zope.component import queryMultiAdapter
from zope.schema.interfaces import IVocabularyFactory

import os


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
