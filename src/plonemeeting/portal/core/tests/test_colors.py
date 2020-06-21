# -*- coding: utf-8 -*-

from plonemeeting.portal.core.tests.portal_test_case import PmPortalDemoFunctionalTestCase
from plone import api


class TestColorCSSView(PmPortalDemoFunctionalTestCase):

    def test_call_in_institution(self):
        portal = self.portal["belleville"]
        view_content = portal.restrictedTraverse("@@custom_colors.css")()
        self.assertTrue("--main-nav-color:" in view_content)
        self.assertTrue("--main-nav-text-color:" in view_content)

        portal = self.meeting
        view_content = portal.restrictedTraverse("@@custom_colors.css")()
        self.assertTrue("--main-nav-color:" in view_content)
        self.assertTrue("--main-nav-text-color:" in view_content)

        portal = self.item
        view_content = portal.restrictedTraverse("@@custom_colors.css")()
        self.assertTrue("--main-nav-color:" in view_content)
        self.assertTrue("--main-nav-text-color:" in view_content)

    def test_call_outside_institution(self):
        portal = api.portal.get()
        view_content = portal.restrictedTraverse("@@custom_colors.css")()
        self.assertTrue(len(view_content) == 0)
