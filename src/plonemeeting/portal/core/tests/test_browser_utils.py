# -*- coding: utf-8 -*-

from plone.api.exc import InvalidParameterError

from plonemeeting.portal.core.config import APP_FOLDER_ID
from plonemeeting.portal.core.tests.portal_test_case import (
    PmPortalDemoFunctionalTestCase,
)


class TestBrowserUtils(PmPortalDemoFunctionalTestCase):
    @property
    def belleville(self):
        return self.portal["belleville"]

    def test_is_institution(self):
        institution_utils = self.belleville.restrictedTraverse("@@utils_view")
        self.assertTrue(institution_utils.is_institution())
        meetings_utils = self.belleville[APP_FOLDER_ID].restrictedTraverse("@@utils_view")
        self.assertFalse(meetings_utils.is_institution())

    def test_get_linked_meeting(self):
        request = self.portal.REQUEST
        utils_view = self.portal.restrictedTraverse("@@utils_view")
        # do not crash when no meeting
        self.assertEqual(None, utils_view.get_linked_meeting())
        meeting = self.belleville["16-novembre-2018-08-30"]
        request.set("seance[]", meeting.UID())
        self.assertEqual(meeting, utils_view.get_linked_meeting())
        # Also works with empty meeting.
        meeting = self.create_object("Meeting")
        request.set("seance[]", meeting.UID())
        self.login_as_manager()
        utils_view = self.portal.restrictedTraverse("@@utils_view")
        self.assertEqual(meeting, utils_view.get_linked_meeting())

    def test_get_plonemeeting_last_modified_on_item(self):
        item = self.belleville["16-novembre-2018-08-30"]["approbation-du-pv-du-xxx"]
        utils_view = item.restrictedTraverse("@@utils_view")
        self.assertEqual(
            "16/11/2018 08:30:00", utils_view.get_plonemeeting_last_modified()
        )

    def test_get_plonemeeting_last_modified_on_meeting(self):
        meeting = self.belleville["16-novembre-2018-08-30"]
        utils_view = meeting.restrictedTraverse("@@utils_view")
        self.assertEqual(
            "16/11/2018 08:30:00", utils_view.get_plonemeeting_last_modified()
        )

    def test_get_meeting_url_by_meeting(self):
        meeting = self.belleville["16-novembre-2018-08-30"]
        utils_view = meeting.restrictedTraverse("@@utils_view")
        expected_url = "http://nohost/plone/belleville/{0}#seance={1}".format(
            APP_FOLDER_ID, meeting.UID()
        )
        self.assertEqual(expected_url, utils_view.get_meeting_url(meeting=meeting))

    def test_get_meeting_url_by_UID(self):
        meeting = self.belleville["16-novembre-2018-08-30"]
        utils_view = meeting.restrictedTraverse("@@utils_view")
        expected_url = "http://nohost/plone/belleville/{0}#seance={1}".format(
            APP_FOLDER_ID, meeting.UID()
        )
        self.assertEqual(expected_url, utils_view.get_meeting_url(UID=meeting.UID()))

    def test_get_meeting_url_by_both(self):
        meeting = self.belleville["16-novembre-2018-08-30"]
        utils_view = meeting.restrictedTraverse("@@utils_view")
        self.assertRaises(
            InvalidParameterError,
            utils_view.get_meeting_url,
            meeting=meeting,
            UID=meeting.UID(),
        )

    def test_get_state(self):
        meeting = self.belleville["16-novembre-2018-08-30"]
        utils_view = meeting.restrictedTraverse("@@utils_view")
        self.assertEqual("decision", utils_view.get_state(meeting))

    def test_get_categories_mappings_value(self):
        meeting = self.belleville["16-novembre-2018-08-30"]
        utils_view = meeting.restrictedTraverse("@@utils_view")
        self.assertEqual(
            "Informatique", utils_view.get_categories_mappings_value("informatique")
        )
