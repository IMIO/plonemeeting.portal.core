from plone import api
from plone.testing.zope import Browser
from plonemeeting.portal.core.tests.portal_test_case import PmPortalDemoFunctionalTestCase

import json


class TestRestViews(PmPortalDemoFunctionalTestCase):

    def test_rest_institution_locations_api_view(self):
        """Test if the values from InstitutionLocationsView are correct"""
        portal = api.portal.get()

        view = portal.unrestrictedTraverse("@@institution-locations")
        render = view()
        # Institutions with imaginary name are ignored
        self.assertDictEqual({}, json.loads(render))

        self.login_as_admin()
        namur = api.content.create(container=self.portal, type="Institution", id="namur", title="Namur")
        liege = api.content.create(container=self.portal, type="Institution", id="liege", title="Liège")
        view = portal.unrestrictedTraverse("@@institution-locations")
        render = view()
        # Not published institutions are ignored too
        self.assertDictEqual({}, json.loads(render))

        api.content.transition(obj=namur, transition="publish")
        api.content.transition(obj=liege, transition="publish")
        # We should have some data now :
        view = portal.unrestrictedTraverse("@@institution-locations")
        render = view()
        json_response = json.loads(render)
        self.assertIn("namur", json_response.keys())
        self.assertIn("liege", json_response.keys())
        self.assertIn("data", json_response["namur"].keys())
        self.assertIn("geo_shape", json_response["namur"]["data"]["fields"].keys())

        # Test if portal as saved locations from remote API for future use
        self.assertTrue(hasattr(portal, "api_institution_locations"))

    def test_rest_meeting_agenda_api_view(self):
        """Test if the values from MeetingAgendaAPIView are correct"""
        meeting = self.portal["belleville"].decisions.listFolderContents({"portal_type": "Meeting"})[0]
        browser = Browser(self.layer["app"])
        browser.handleErrors = False

        # Construct the URL to the view
        url = f"{meeting.absolute_url()}/@@agenda"
        browser.open(url)

        self.assertEqual(browser.headers.get("Content-Type"), "application/json")
        data = json.loads(browser.contents)

        self.assertEqual(len(data), 3)
        self.assertIn("formatted_title", data[0])
        self.assertDictEqual(
            data[0]["formatted_title"],
            {"content-type": "text/html", "data": "<p>Approbation du PV du XXX</p>", "encoding": "utf-8"},
        )
        self.assertEqual(data[0]["number"], "1")
        self.assertEqual(data[0]["number"], "1")
        self.assertEqual(data[0]["number"], "1")

        titles = [item["title"] for item in data]
        self.assertIn("Point tourisme", titles)
        self.assertIn("Point tourisme urgent", titles)

    def test_prometheus_exporter(self):
        """Test if the values from PrometheusExporter are correct"""
        view = self.portal.unrestrictedTraverse("@@prometheus-export")
        render = view()
        request = self.portal.REQUEST
        self.assertEqual(request.response.getHeader("Content-type"), "text/plain; charset=utf-8")

        # Parse the output metrics
        metrics = dict()
        for line in render.split("\n"):
            if line and not line.startswith("#"):
                key, value = line.split(" ")
                metrics[key] = float(value)

        self.assertIn("publications_published", metrics)
        self.assertIn("publications_planned", metrics)
        self.assertIn("publications_planned_late", metrics)
        self.assertIn("publications_expired", metrics)
        self.assertIn("publications_expired_late", metrics)
        self.assertIn("dangling_publications", metrics)

        expected_published = len(
            self.portal.portal_catalog.unrestrictedSearchResults(portal_type="Publication", review_state="published")
        )
        self.assertEqual(metrics["publications_published"], expected_published)

        expected_planned = len(
            self.portal.portal_catalog.unrestrictedSearchResults(portal_type="Publication", review_state="planned")
        )
        self.assertEqual(metrics["publications_planned"], expected_planned)
