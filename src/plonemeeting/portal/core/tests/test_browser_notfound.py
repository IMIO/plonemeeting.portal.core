from plone import api
from plone.testing.zope import Browser
from plonemeeting.portal.core.tests import PM_USER_PASSWORD
from plonemeeting.portal.core.tests.portal_test_case import PmPortalDemoFunctionalTestCase

import transaction


class TestNotFoundView(PmPortalDemoFunctionalTestCase):
    """The 404 page, for missing content and for hidden content."""

    def setUp(self):
        super().setUp()
        self.private_publication = self.institution.publications["publication-28"]
        # A member without access to the institution.
        self.portal.acl_users._doAddUser("plain-member", PM_USER_PASSWORD, [], [])
        transaction.commit()

    def _browser(self, auth=None):
        browser = Browser(self.layer["app"])
        browser.handleErrors = True
        browser.raiseHttpErrors = False
        # Without this header, the exception view returns JSON.
        browser.addHeader("Accept", "text/html")
        if auth:
            browser.addHeader("Authorization", f"Basic {auth}:{PM_USER_PASSWORD}")
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
        # The page uses main_template.
        self.assertIn("visual-portal-wrapper", self._contents(browser))
        self.assertIn("Cette page n'existe pas ou plus", self._contents(browser))
        # The button goes to the portal home page.
        self.assertIn(f'href="{portal.absolute_url()}"', self._contents(browser))

    def test_404_inside_institution_links_back_to_institution(self):
        browser = self._browser()
        browser.open(self.institution.absolute_url() + "/no-such-page")

        self.assertEqual("404 Not Found", browser.headers.get("status"))
        self.assertIn("Cette page n'existe pas ou plus", self._contents(browser))
        # The button goes to the institution.
        self.assertIn(f'href="{self.institution.absolute_url()}"', self._contents(browser))
        self.assertIn(self.institution.Title(), self._contents(browser))

    def test_anonymous_on_private_content_gets_404_not_login(self):
        browser = self._browser()
        browser.open(self.private_publication.absolute_url())

        self.assertEqual("404 Not Found", browser.headers.get("status"))
        self.assertNotIn("login", browser.url)
        self.assertIn("Cette page n'existe pas ou plus", self._contents(browser))

        # The response is the same as for content that does not exist.
        missing = self._browser()
        missing.open(self.private_publication.absolute_url() + "-missing")
        self.assertEqual(self._contents(missing), self._contents(browser))
        self.assertEqual(sorted(missing.headers.keys()), sorted(browser.headers.keys()))

    def test_authenticated_unauthorized_is_unchanged(self):
        # A member without access gets the usual login challenge.
        browser = self._browser(auth="plain-member")
        browser.open(self.private_publication.absolute_url())

        self.assertNotEqual("404 Not Found", browser.headers.get("status"))
        self.assertNotIn("Cette page n'existe pas ou plus", self._contents(browser))
