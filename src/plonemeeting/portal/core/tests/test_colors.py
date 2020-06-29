# -*- coding: utf-8 -*-

from plonemeeting.portal.core.tests.portal_test_case import PmPortalDemoFunctionalTestCase
from plone import api


class TestColorCSSView(PmPortalDemoFunctionalTestCase):
# TODO : need more tests

    def test_render_custom_css(self):
        view_content = api.portal.get().unrestrictedTraverse("@@custom_colors.css").render()
        self.assertTrue("--main-nav-color:" in view_content)
        self.assertTrue("--main-nav-text-color:" in view_content)
