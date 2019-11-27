# -*- coding: utf-8 -*-
import json
import os
import unittest

from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plonemeeting.portal.core.browser.sync import sync_items
from plonemeeting.portal.core.browser.sync import sync_meeting
from plonemeeting.portal.core.content.meeting import IMeeting
from plonemeeting.portal.core.testing import (
    PLONEMEETING_PORTAL_CORE_INTEGRATION_TESTING,
)
from zope.component import getMultiAdapter


class TestMeetingSynchronization(unittest.TestCase):
    layer = PLONEMEETING_PORTAL_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.institution = api.content.create(
            container=self.portal, type="Institution", id="institution"
        )
        self.to_localized_time = getMultiAdapter(
            (self.institution, self.layer["request"]), name="plone"
        ).toLocalizedTime
        with open(
            os.path.join(os.path.dirname(__file__), "resources/meeting_mock.json")
        ) as json_file:
            self.json_meeting = json.load(json_file)
        with open(
            os.path.join(os.path.dirname(__file__), "resources/meeting_items_mock.json")
        ) as json_file:
            self.json_meeting_items = json.load(json_file)

    def test_sync_meeting(self):
        meeting = sync_meeting(
            self.to_localized_time, self.institution, self.json_meeting.get("items")[0]
        )
        self.assertTrue(
            IMeeting.providedBy(meeting),
            u"IMeeting not provided by {0}!".format(meeting),
        )

    def test_sync_meeting_items(self):
        meeting = sync_meeting(
            self.to_localized_time, self.institution, self.json_meeting.get("items")[0]
        )
        results = sync_items(self.to_localized_time, meeting, self.json_meeting_items)
        self.assertEqual(len(meeting.items()), results.get("created"))

    def test_sync_with_updates_meeting_items(self):
        meeting = sync_meeting(
            self.to_localized_time, self.institution, self.json_meeting.get("items")[0]
        )
        # results {'deleted': 0, 'modified': 0, 'created': 28}
        results = sync_items(self.to_localized_time, meeting, self.json_meeting_items)
        self.assertEqual(len(meeting.items()), results.get("created"))
        decision = {"content-type": "text/html", "data": u"<p>Nouvelle décision</p>"}
        modification_date = {"modification_date": u"2019-11-26T14:42:40+00:00"}
        self.json_meeting_items.get("items")[0].get("decision").update(decision)
        self.json_meeting_items.get("items")[0].update(modification_date)
        results = sync_items(self.to_localized_time, meeting, self.json_meeting_items)
        self.assertEqual(results.get("created"), 0)
        self.assertEqual(results.get("modified"), 1)

    def test_sync_no_modif_date_no_update(self):
        meeting = sync_meeting(
            self.to_localized_time, self.institution, self.json_meeting.get("items")[0]
        )
        results = sync_items(self.to_localized_time, meeting, self.json_meeting_items)
        decision = {"content-type": "text/html", "data": u"<p>Nouvelle décision</p>"}
        self.json_meeting_items.get("items")[0].get("decision").update(decision)
        results = sync_items(self.to_localized_time, meeting, self.json_meeting_items)
        self.assertEqual(results.get("created"), 0)
        self.assertEqual(results.get("modified"), 0)
