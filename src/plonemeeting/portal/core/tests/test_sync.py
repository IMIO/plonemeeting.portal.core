# -*- coding: utf-8 -*-
import json
import os
import pytz
import unittest

from datetime import datetime
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plonemeeting.portal.core.browser.sync import (
    sync_items_data,
    get_decision_from_json,
)
from plonemeeting.portal.core.browser.sync import sync_meeting_data
from plonemeeting.portal.core.content.meeting import IMeeting
from plonemeeting.portal.core.testing import PLONEMEETING_PORTAL_DEMO_FUNCTIONAL_TESTING


class TestMeetingSynchronization(unittest.TestCase):
    layer = PLONEMEETING_PORTAL_DEMO_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.institution = api.content.find(id="amityville")[0].getObject()
        self.meeting = api.content.find(self.institution, portal_type="Meeting")[
            0
        ].getObject()
        self.item = api.content.find(self.meeting, portal_type="Item")[0].getObject()
        with open(
            os.path.join(os.path.dirname(__file__), "resources/meeting_mock.json")
        ) as json_file:
            self.json_meeting = json.load(json_file)
        with open(
            os.path.join(os.path.dirname(__file__), "resources/meeting_items_mock.json")
        ) as json_file:
            self.json_meeting_items = json.load(json_file)

    def test_sync_meeting_data(self):
        meeting = sync_meeting_data(
            self.institution, self.json_meeting.get("items")[0]
        )
        self.assertTrue(
            IMeeting.providedBy(meeting),
            u"IMeeting not provided by {0}!".format(meeting),
        )
        timezone = api.portal.get_registry_record('plone.portal_timezone')
        self.assertEqual(timezone, 'UTC')
        date_time = datetime(2019, 11, 9, 23, 0)
        date_time = date_time.astimezone(pytz.timezone(timezone))
        self.assertEqual(meeting.date_time, date_time)

    def test_sync_meeting_items(self):
        meeting = sync_meeting_data(
            self.institution, self.json_meeting.get("items")[0]
        )
        results = sync_items_data(
            meeting, self.json_meeting_items, self.institution
        )
        self.assertEqual(len(meeting.items()), results.get("created"))

    def test_sync_with_updates_meeting_items(self):
        meeting = sync_meeting_data(
            self.institution, self.json_meeting.get("items")[0]
        )
        # results {'deleted': 0, 'modified': 0, 'created': 28}
        results = sync_items_data(
            meeting, self.json_meeting_items, self.institution
        )
        self.assertEqual(len(meeting.items()), results.get("created"))
        decision = {"content-type": "text/html", "data": u"<p>Nouvelle décision</p>"}
        modification_date = {"modification_date": u"2019-11-26T14:42:40+00:00"}
        self.json_meeting_items.get("items")[0].get("decision").update(decision)
        self.json_meeting_items.get("items")[0].update(modification_date)
        results = sync_items_data(
            meeting, self.json_meeting_items, self.institution
        )
        self.assertEqual(results.get("created"), 0)
        self.assertEqual(results.get("modified"), 1)

    def test_sync_no_modif_date_no_update(self):
        meeting = sync_meeting_data(
            self.institution, self.json_meeting.get("items")[0]
        )
        results = sync_items_data(
            meeting, self.json_meeting_items, self.institution
        )
        decision = {"content-type": "text/html", "data": u"<p>Nouvelle décision</p>"}
        self.json_meeting_items.get("items")[0].get("decision").update(decision)
        results = sync_items_data(
            meeting, self.json_meeting_items, self.institution
        )
        self.assertEqual(results.get("created"), 0)
        self.assertEqual(results.get("modified"), 0)

    def test_get_decision_from_json(self):
        item_jsons = self.json_meeting_items.get("items")

        self.assertRaises(
            AttributeError, get_decision_from_json, "", self.item, item_jsons[0]
        )
        item_json = item_jsons[0]
        self.assertEqual(
            get_decision_from_json(
                u"python: json['decision']['data']", self.item, item_json
            ),
            item_jsons[0]["decision"]["data"],
        )
        item_json = item_jsons[1]
        self.assertEqual(
            get_decision_from_json(
                u"python: '{}<p>DECIDE</p>{}'.format("
                u"json['motivation']['data'], json['decision']['data'])",
                self.item,
                item_json,
            ),
            u"{}<p>DECIDE</p>{}".format(
                item_json["motivation"]["data"], item_json["decision"]["data"]
            ),
        )
