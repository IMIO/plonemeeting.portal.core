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

    def _shared_link_response(self, site_id, token):
        shared_link_url = "https://plausible.imio.be/share/{}?auth={}".format(site_id.replace("/", "%2F"), token)
        return mock({"status_code": 200, "json": lambda: {"name": "Statistiques", "url": shared_link_url}, "text": ""})

    def _mock_plausible_api(self, site_id, token):
        """Happy path: the idempotent shared-link call succeeds straight away,
        so the site never needs to be (re)created."""
        when(requests).put(
            SHARED_LINKS_URL,
            json={"site_id": site_id, "name": f"Statistiques {site_id}"},
            headers=API_HEADERS,
            timeout=TIMEOUT,
        ).thenReturn(self._shared_link_response(site_id, token))

    def _verify_shared_link_calls(self, site_id, times):
        verify(requests, times=times).put(
            SHARED_LINKS_URL,
            json={"site_id": site_id, "name": f"Statistiques {site_id}"},
            headers=API_HEADERS,
            timeout=TIMEOUT,
        )

    def test_institution_statistics_renders_dashboard(self):
        site_id = "deliberations.be/amityville"
        self._mock_plausible_api(site_id, "amityville-token")
        self.login_as_institution_manager()
        view = self.institution.restrictedTraverse("@@statistics")
        html = view()
        self.assertIsNone(view.error_message)
        self.assertIn("plausible-embed", html)
        # & is escaped as &amp; in the rendered src attribute
        self.assertIn(
            "https://plausible.imio.be/share/deliberations.be%2Famityville"
            "?auth=amityville-token&amp;embed=true&amp;theme=light&amp;background=transparent",
            html,
        )
        self.assertIn("https://plausible.imio.be/js/embed.host.js", html)

    def test_institution_statistics_reprovisions_on_every_load(self):
        # The token is never cached: each access re-provisions the shared link,
        # so the dashboard self-heals if the link is invalidated on Plausible's
        # side. Two accesses must hit the shared-links API twice.
        site_id = "deliberations.be/amityville"
        self._mock_plausible_api(site_id, "amityville-token")
        self.login_as_institution_manager()
        view = self.institution.restrictedTraverse("@@statistics")
        view()
        view()
        self._verify_shared_link_calls(site_id, times=2)

    def test_institution_statistics_provisions_missing_site(self):
        # When the site does not exist yet, the first shared-link call fails;
        # the site is then created and the call retried.
        site_id = "deliberations.be/amityville"
        when(requests).post(
            SITES_URL, json={"domain": site_id}, headers=API_HEADERS, timeout=TIMEOUT
        ).thenReturn(mock({"status_code": 201, "json": lambda: {"domain": site_id}, "text": ""}))
        when(requests).put(
            SHARED_LINKS_URL,
            json={"site_id": site_id, "name": f"Statistiques {site_id}"},
            headers=API_HEADERS,
            timeout=TIMEOUT,
        ).thenReturn(
            mock({"status_code": 404, "json": lambda: {}, "text": "site not found"})
        ).thenReturn(self._shared_link_response(site_id, "amityville-token"))
        self.login_as_institution_manager()
        view = self.institution.restrictedTraverse("@@statistics")
        html = view()
        verify(requests, times=1).post(SITES_URL, json={"domain": site_id}, headers=API_HEADERS, timeout=TIMEOUT)
        self.assertIsNone(view.error_message)
        self.assertIn("plausible-embed", html)

    def test_institution_statistics_without_api_key(self):
        api.portal.set_registry_record("plonemeeting.portal.core.plausible_api_key", "")
        self.login_as_institution_manager()
        view = self.institution.restrictedTraverse("@@statistics")
        html = view()
        self.assertIsNotNone(view.error_message)
        self.assertNotIn("plausible-embed", html)

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

    def test_institution_statistics_requires_modify_permission(self):
        self.logout()
        with self.assertRaises(Unauthorized):
            self.institution.restrictedTraverse("@@statistics")

    def test_controlpanel_statistics_renders_dashboard(self):
        site_id = "deliberations.be"
        self._mock_plausible_api(site_id, "global-token")
        self.login_as_admin()
        view = self.portal.restrictedTraverse("@@plausible-statistics")
        html = view()
        self.assertIsNone(view.error_message)
        self.assertIn("plausible-embed", html)
        self.assertIn(
            "https://plausible.imio.be/share/deliberations.be"
            "?auth=global-token&amp;embed=true&amp;theme=light&amp;background=transparent",
            html,
        )
        # the token is not cached: a second access re-provisions the link
        view()
        self._verify_shared_link_calls(site_id, times=2)

    def test_controlpanel_statistics_requires_manage_portal(self):
        self.login_as_institution_manager()
        with self.assertRaises(Unauthorized):
            self.portal.restrictedTraverse("@@plausible-statistics")
