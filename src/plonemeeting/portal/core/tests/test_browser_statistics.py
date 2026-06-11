# -*- coding: utf-8 -*-
from AccessControl import Unauthorized
from mockito import mock
from mockito import unstub
from mockito import verify
from mockito import when
from plone import api
from plonemeeting.portal.core.tests.portal_test_case import PmPortalDemoFunctionalTestCase

import requests


API_HEADERS = {"Authorization": "Bearer test-api-key", "Content-Type": "application/json"}
SITES_URL = "https://plausible.imio.be/api/v1/sites"
SHARED_LINKS_URL = "https://plausible.imio.be/api/v1/sites/shared-links"
TIMEOUT = 10


class TestBrowserStatistics(PmPortalDemoFunctionalTestCase):
    def setUp(self):
        super().setUp()
        api.portal.set_registry_record("plonemeeting.portal.core.plausible_api_key", "test-api-key")

    def tearDown(self):
        unstub()
        super().tearDown()

    def _mock_plausible_api(self, site_id, token, create_site_status=200):
        shared_link_url = "https://plausible.imio.be/share/{}?auth={}".format(site_id.replace("/", "%2F"), token)
        when(requests).post(
            SITES_URL, json={"domain": site_id}, headers=API_HEADERS, timeout=TIMEOUT
        ).thenReturn(
            mock({"status_code": create_site_status, "json": lambda: {"domain": site_id}, "text": "mocked"})
        )
        when(requests).put(
            SHARED_LINKS_URL,
            json={"site_id": site_id, "name": f"Statistiques {site_id}"},
            headers=API_HEADERS,
            timeout=TIMEOUT,
        ).thenReturn(
            mock({"status_code": 200, "json": lambda: {"name": "Statistiques", "url": shared_link_url}, "text": ""})
        )

    def _verify_shared_link_calls(self, site_id, times):
        verify(requests, times=times).put(
            SHARED_LINKS_URL,
            json={"site_id": site_id, "name": f"Statistiques {site_id}"},
            headers=API_HEADERS,
            timeout=TIMEOUT,
        )

    def test_institution_statistics_provisions_and_caches_token(self):
        site_id = "deliberations.be/amityville"
        self._mock_plausible_api(site_id, "amityville-token")
        self.login_as_institution_manager()
        view = self.institution.restrictedTraverse("@@statistics")
        html = view()
        self.assertEqual(self.institution.plausible_shared_link_token, "amityville-token")
        self.assertIn("plausible-embed", html)
        # & is escaped as &amp; in the rendered src attribute
        self.assertIn(
            "https://plausible.imio.be/share/deliberations.be%2Famityville"
            "?auth=amityville-token&amp;embed=true&amp;theme=light&amp;background=transparent",
            html,
        )
        self.assertIn("https://plausible.imio.be/js/embed.host.js", html)
        # a second access reuses the stored token: no further API call
        view()
        self._verify_shared_link_calls(site_id, times=1)

    def test_institution_statistics_tolerates_existing_site(self):
        # Plausible answers an error on site creation when the domain already
        # exists: the shared link must still be fetched and displayed.
        site_id = "deliberations.be/amityville"
        self._mock_plausible_api(site_id, "amityville-token", create_site_status=400)
        self.login_as_institution_manager()
        view = self.institution.restrictedTraverse("@@statistics")
        html = view()
        self.assertEqual(self.institution.plausible_shared_link_token, "amityville-token")
        self.assertIn("plausible-embed", html)

    def test_institution_statistics_without_api_key(self):
        api.portal.set_registry_record("plonemeeting.portal.core.plausible_api_key", "")
        self.login_as_institution_manager()
        view = self.institution.restrictedTraverse("@@statistics")
        html = view()
        self.assertIsNotNone(view.error_message)
        self.assertNotIn("plausible-embed", html)
        self.assertFalse(getattr(self.institution, "plausible_shared_link_token", None))

    def test_institution_statistics_api_failure(self):
        site_id = "deliberations.be/amityville"
        when(requests).post(
            SITES_URL, json={"domain": site_id}, headers=API_HEADERS, timeout=TIMEOUT
        ).thenReturn(mock({"status_code": 200, "json": lambda: {}, "text": ""}))
        when(requests).put(
            SHARED_LINKS_URL,
            json={"site_id": site_id, "name": f"Statistiques {site_id}"},
            headers=API_HEADERS,
            timeout=TIMEOUT,
        ).thenReturn(mock({"status_code": 500, "json": lambda: {}, "text": "mocked error"}))
        self.login_as_institution_manager()
        view = self.institution.restrictedTraverse("@@statistics")
        html = view()
        self.assertIsNotNone(view.error_message)
        self.assertNotIn("plausible-embed", html)
        self.assertFalse(getattr(self.institution, "plausible_shared_link_token", None))

    def test_institution_statistics_requires_modify_permission(self):
        self.logout()
        with self.assertRaises(Unauthorized):
            self.institution.restrictedTraverse("@@statistics")

    def test_controlpanel_statistics_provisions_and_caches_token(self):
        site_id = "deliberations.be"
        self._mock_plausible_api(site_id, "global-token")
        self.login_as_admin()
        view = self.portal.restrictedTraverse("@@plausible-statistics")
        html = view()
        self.assertEqual(
            api.portal.get_registry_record("plonemeeting.portal.core.plausible_shared_link_token"),
            "global-token",
        )
        self.assertIn("plausible-embed", html)
        self.assertIn(
            "https://plausible.imio.be/share/deliberations.be"
            "?auth=global-token&amp;embed=true&amp;theme=light&amp;background=transparent",
            html,
        )
        # a second access reuses the cached token: no further API call
        view()
        self._verify_shared_link_calls(site_id, times=1)

    def test_controlpanel_statistics_requires_manage_portal(self):
        self.login_as_institution_manager()
        with self.assertRaises(Unauthorized):
            self.portal.restrictedTraverse("@@plausible-statistics")
