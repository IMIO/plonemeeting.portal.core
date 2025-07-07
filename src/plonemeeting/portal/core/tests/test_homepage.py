# -*- coding: utf-8 -*-
from plone import api
from plone.testing.zope import Browser
from plonemeeting.portal.core.tests.portal_test_case import PmPortalDemoFunctionalTestCase

import json


class TestHomepageView(PmPortalDemoFunctionalTestCase):

    def test_homepage_view(self):
        """ Test if the homepage is rendered correctly and if it doesn't fail"""
        portal = api.portal.get()
        app = self.layer["app"]
        browser = Browser(app)
        browser.open(portal.absolute_url())
        html_content = browser.contents

        self.assertEqual(
            "200 OK",
            browser.headers.get('status')
        )

        self.assertIn("x-institution-map", html_content)
        self.assertIn("x-institution-select", html_content)

    def test_get_json_institution_type_vocabulary(self):
        """ Test if the institution_type vocabulary is correctly returned"""
        portal = api.portal.get()
        view = portal.unrestrictedTraverse("homepage_view")
        vocabulary_values = api.portal.get_registry_record("plonemeeting.portal.core.institution_types")
        json_str = view.get_json_institution_type_vocabulary()
        result = json.loads(json_str)
        self.assertEqual(len(result["items"]), len(vocabulary_values.items()))
        for value in result["items"]:
            self.assertEqual(value["title"], vocabulary_values[value["token"]])

    def test_sitemap_view(self):
        """ Test if the sitemap view is accessible and returns a 200 status code"""
        portal = api.portal.get()
        app = self.layer["app"]
        browser = Browser(app)
        browser.open(portal.absolute_url() + "/sitemap")

        self.assertEqual(
            "200 OK",
            browser.headers.get('status')
        )
