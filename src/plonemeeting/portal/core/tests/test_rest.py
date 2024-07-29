from plone import api
from plone.testing.zope import Browser
from plonemeeting.portal.core.tests.portal_test_case import PmPortalDemoFunctionalTestCase
import json


class TestRestViews(PmPortalDemoFunctionalTestCase):
    def test_site_InstitutionLocationsAPIView(self):
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
        # We should have some data now :
        view = portal.unrestrictedTraverse("@@institution_locations")
        render = view()
        json_response = json.loads(render)
        self.assertIn("namur", json_response.keys())
        self.assertIn("liege", json_response.keys())
        self.assertIn("data", json_response["namur"].keys())
        self.assertIn("geo_shape", json_response["namur"]["data"]["fields"].keys())

        # Test if portal as saved locations from remote API for future use
        self.assertTrue(hasattr(portal, "api_institution_locations"))


    def test_meeting_MeetingAgendaAPIView(self):
        meeting = self.portal["belleville"].listFolderContents(
            {"portal_type": "Meeting"})[0]
        request = self.portal.REQUEST
        view = meeting.restrictedTraverse("@@view")
