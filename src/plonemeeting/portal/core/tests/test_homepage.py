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

    def test_institution_locations_view(self):
        """ Test if the values from InstitutionLocationsView are correct"""
        portal = api.portal.get()

        view = portal.unrestrictedTraverse("@@institution_locations")
        render = view()
        # Institutions with imaginary name are ignored
        self.assertDictEqual({}, json.loads(render))

        self.login_as_manager()
        namur = api.content.create(
            container=self.portal, type="Institution", id="namur", title="Namur"
        )
        liege = api.content.create(
            container=self.portal, type="Institution", id="liege", title="Liège"
        )
        view = portal.unrestrictedTraverse("@@institution_locations")
        render = view()
        # Not published institutions are ignored too
        self.assertDictEqual({}, json.loads(render))
        api.content.transition(obj=namur, transition='publish')
        api.content.transition(obj=liege, transition='publish')

        view = portal.unrestrictedTraverse("@@institution_locations")
        render = view()
        json_response = json.loads(render)
        # We should have some data now :
        self.assertIn("namur", json_response.keys())
        self.assertIn("liege", json_response.keys())
        self.assertIn("data", json_response["namur"].keys())
        self.assertIn("geo_shape", json_response["namur"]["data"]["fields"].keys())
