# -*- coding: utf-8 -*-
from plone import api
from plone.testing.zope import Browser
from plonemeeting.portal.core.tests import PM_USER_PASSWORD
from plonemeeting.portal.core.tests.portal_test_case import PmPortalDemoFunctionalTestCase

import transaction


class TestNotFoundView(PmPortalDemoFunctionalTestCase):
    """DELIBE-313: themed 404 page + anonymous Unauthorized -> 404."""

    def setUp(self):
        super().setUp()
        self.private_publication = self.institution.publications["publication-28"]
        # A plain, authenticated Member with no access to the institution.
        self.portal.acl_users._doAddUser("plain-member", PM_USER_PASSWORD, [], [])
        transaction.commit()

    def _browser(self, auth=None):
        browser = Browser(self.layer["app"])
        browser.handleErrors = True
        browser.raiseHttpErrors = False
        # Behave like a real browser so the exception view renders HTML
        # (without this header ExceptionView returns its JSON branch).
        browser.addHeader("Accept", "text/html")
        if auth:
            browser.addHeader("Authorization", "Basic {0}:{1}".format(auth, PM_USER_PASSWORD))
        return browser

    @staticmethod
    def _contents(browser):
        body = browser.contents
        return body.decode("utf-8") if isinstance(body, bytes) else body

    def test_404_at_portal_root_is_themed_and_links_home(self):
        portal = api.portal.get()
        browser = self._browser()
        browser.open(portal.absolute_url() + "/no-such-thing")

        self.assertEqual("404 Not Found", browser.headers.get("status"))
        # Rendered through main_template (so Diazo themes it in production):
        self.assertIn("visual-portal-wrapper", self._contents(browser))
        self.assertIn("Cette page n'existe pas ou plus", self._contents(browser))
        # Back button targets the portal homepage:
        self.assertIn('href="{0}"'.format(portal.absolute_url()), self._contents(browser))

    def test_404_inside_institution_links_back_to_institution(self):
        browser = self._browser()
        browser.open(self.institution.absolute_url() + "/no-such-page")

        self.assertEqual("404 Not Found", browser.headers.get("status"))
        self.assertIn("Cette page n'existe pas ou plus", self._contents(browser))
        # Back button targets the institution the user was inside:
        self.assertIn('href="{0}"'.format(self.institution.absolute_url()), self._contents(browser))
        self.assertIn(self.institution.Title(), self._contents(browser))

    def test_anonymous_on_private_content_gets_404_not_login(self):
        browser = self._browser()
        browser.open(self.private_publication.absolute_url())

        self.assertEqual("404 Not Found", browser.headers.get("status"))
        # Not redirected to the login form (no information leak):
        self.assertNotIn("login", browser.url)
        self.assertNotIn("require_login", browser.url)
        self.assertIn("Cette page n'existe pas ou plus", self._contents(browser))

    def test_authenticated_unauthorized_is_unchanged(self):
        # A logged-in member without access is NOT turned into a 404; they keep
        # Plone's normal behaviour (insufficient-privileges / login challenge).
        browser = self._browser(auth="plain-member")
        browser.open(self.private_publication.absolute_url())

        self.assertNotEqual("404 Not Found", browser.headers.get("status"))
        self.assertNotIn("Cette page n'existe pas ou plus", self._contents(browser))

    def test_notfound_view_resolves_institution(self):
        view = self.institution.restrictedTraverse("@@notfound")
        self.assertEqual(view.get_institution(), self.institution)
        self.assertEqual(view.back_url(), self.institution.absolute_url())
        self.assertTrue(view.is_in_institution())

    def test_notfound_view_falls_back_to_homepage(self):
        portal = api.portal.get()
        view = portal.restrictedTraverse("@@notfound")
        self.assertIsNone(view.get_institution())
        self.assertEqual(view.back_url(), portal.absolute_url())
        self.assertFalse(view.is_in_institution())
