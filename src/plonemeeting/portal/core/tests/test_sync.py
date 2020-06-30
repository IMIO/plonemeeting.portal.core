# -*- coding: utf-8 -*-
import json
import os
from datetime import datetime

import pytz
from plone import api
from plonemeeting.portal.core.browser.sync import (
    sync_items_data,
    sync_annexes_data,
    get_formatted_data_from_json,
)
from plonemeeting.portal.core.browser.sync import sync_meeting_data
from plonemeeting.portal.core.content.meeting import IMeeting
from plonemeeting.portal.core.tests.portal_test_case import (
    PmPortalDemoFunctionalTestCase,
)


class TestMeetingSynchronization(PmPortalDemoFunctionalTestCase):
    def setUp(self):
        super().setUp()
        with open(
            os.path.join(os.path.dirname(__file__), "resources/meeting_mock.json")
        ) as json_file:
            self.json_meeting = json.load(json_file)
        with open(
            os.path.join(os.path.dirname(__file__), "resources/meeting_items_mock.json")
        ) as json_file:
            self.json_meeting_items = json.load(json_file)
        with open(
            os.path.join(
                os.path.dirname(__file__), "resources/annexes_not_publishable_mock.json"
            )
        ) as json_file:
            self.json_annexes_not_publishable_mock = json.load(json_file)
        with open(
            os.path.join(
                os.path.dirname(__file__),
                "resources/annexes_not_publishable_updated_mock.json",
            )
        ) as json_file:
            self.json_annexes_not_publishable_updated_mock = json.load(json_file)
        with open(
            os.path.join(
                os.path.dirname(__file__), "resources/annexes_publishable_mock.json"
            )
        ) as json_file:
            self.json_annexes_publishable_mock = json.load(json_file)
        with open(
            os.path.join(
                os.path.dirname(__file__),
                "resources/annexes_publishable_updated_mock.json",
            )
        ) as json_file:
            self.json_annexes_publishable_updated_mock = json.load(json_file)

    def test_sync_meeting_data(self):
        meeting = sync_meeting_data(self.institution, self.json_meeting.get("items")[0])
        self.assertTrue(
            IMeeting.providedBy(meeting),
            u"IMeeting not provided by {0}!".format(meeting),
        )
        timezone = api.portal.get_registry_record("plone.portal_timezone")
        self.assertEqual(timezone, "UTC")
        date_time = datetime(2019, 11, 9, 23, 0)
        date_time = date_time.astimezone(pytz.timezone(timezone))
        self.assertEqual(meeting.date_time, date_time)

    def test_sync_meeting_items(self):
        meeting = sync_meeting_data(self.institution, self.json_meeting.get("items")[0])
        results = sync_items_data(meeting, self.json_meeting_items, self.institution)
        self.assertEqual(len(meeting.items()), results.get("created"))
        self.assertEqual(meeting.values()[0].number, "1")
        self.assertEqual(meeting.values()[0].sortable_number, 100)
        self.assertEqual(meeting.values()[1].number, "2")
        self.assertEqual(meeting.values()[1].sortable_number, 200)
        self.assertEqual(meeting.values()[10].number, "11")
        self.assertEqual(meeting.values()[10].sortable_number, 1100)
        self.assertEqual(meeting.values()[20].number, "21")
        self.assertEqual(meeting.values()[20].sortable_number, 2100)
        self.assertEqual(meeting.values()[-1].number, "28")
        self.assertEqual(meeting.values()[-1].sortable_number, 2800)

    def test_sync_with_updates_meeting_items(self):
        meeting = sync_meeting_data(self.institution, self.json_meeting.get("items")[0])
        # results {'deleted': 0, 'modified': 0, 'created': 28}
        results = sync_items_data(meeting, self.json_meeting_items, self.institution)
        self.assertEqual(len(meeting.items()), results.get("created"))
        decision = {"content-type": "text/html", "data": u"<p>Nouvelle décision</p>"}
        modification_date = {"modification_date": u"2019-11-26T14:42:40+00:00"}
        self.json_meeting_items.get("items")[0].get("decision").update(decision)
        self.json_meeting_items.get("items")[0].update(modification_date)
        results = sync_items_data(meeting, self.json_meeting_items, self.institution)
        self.assertEqual(results.get("created"), 0)
        self.assertEqual(results.get("modified"), 1)

    def test_sync_no_modif_date_no_update(self):
        meeting = sync_meeting_data(self.institution, self.json_meeting.get("items")[0])
        results = sync_items_data(meeting, self.json_meeting_items, self.institution)
        decision = {"content-type": "text/html", "data": u"<p>Nouvelle décision</p>"}
        self.json_meeting_items.get("items")[0].get("decision").update(decision)
        results = sync_items_data(meeting, self.json_meeting_items, self.institution)
        self.assertEqual(results.get("created"), 0)
        self.assertEqual(results.get("modified"), 0)

    def test_force_sync_item(self):
        meeting = sync_meeting_data(self.institution, self.json_meeting.get("items")[0])
        results = sync_items_data(
            meeting, self.json_meeting_items, self.institution, force=True
        )
        decision = {"content-type": "text/html", "data": u"<p>Nouvelle décision</p>"}
        self.json_meeting_items.get("items")[0].get("decision").update(decision)
        results = sync_items_data(
            meeting, self.json_meeting_items, self.institution, force=True
        )
        self.assertEqual(results.get("created"), 0)
        self.assertEqual(results.get("modified"), 28)
        items = meeting.listFolderContents(contentFilter={"portal_type": "Item"})
        first_item = items[0]
        self.assertEqual(first_item.decision.raw, "<p>Nouvelle décision</p>")

    def test_get_formatted_data_from_json(self):
        item_jsons = self.json_meeting_items.get("items")

        self.assertIsNone(get_formatted_data_from_json("", self.item, item_jsons[0]))
        item_json = item_jsons[0]
        self.assertEqual(
            get_formatted_data_from_json(
                u"python: json['decision']['data']", self.item, item_json
            ),
            item_jsons[0]["decision"]["data"],
        )
        item_json = item_jsons[1]
        self.assertEqual(
            get_formatted_data_from_json(
                u"python: '{}<p>DECIDE</p>{}'.format("
                u"json['motivation']['data'], json['decision']['data'])",
                self.item,
                item_json,
            ),
            u"{}<p>DECIDE</p>{}".format(
                item_json["motivation"]["data"], item_json["decision"]["data"]
            ),
        )

    def test_sync_annexes_publishable_disabled(self):
        self.institution.info_annex_formatting_tal = "python: json['category_title']"
        self.assertEqual(len(self.item.listFolderContents()), 1)
        annex = self.item.listFolderContents()[0]
        # delete existing annex and add the new one
        sync_annexes_data(
            self.item, self.institution, self.json_annexes_not_publishable_mock
        )
        self.assertEqual(len(self.item.listFolderContents()), 1)
        annex2 = self.item.listFolderContents()[0]
        self.assertNotEqual(annex.UID(), annex2.UID())

        file = self.item.listFolderContents()[-1]
        self.assertEqual(file.portal_type, "File")
        self.assertEqual(file.id, "test-annexe")
        self.assertEqual(file.title, "Test Annexe")
        self.assertEqual(file.content_type(), "image/jpeg")

        blobs = file.file
        self.assertEqual(blobs.filename, "test-annexe.jpeg")
        self.assertEqual(blobs.contentType, "image/jpeg")
        self.assertEqual(blobs.size, 103911)
        # test update
        self.assertEqual(len(self.item.listFolderContents()), 1)
        sync_annexes_data(
            self.item, self.institution, self.json_annexes_not_publishable_updated_mock
        )
        self.assertEqual(len(self.item.listFolderContents()), 1)
        file = self.item.listFolderContents()[-1]
        self.assertEqual(file.portal_type, "File")
        self.assertEqual(file.id, "test-annexe")
        self.assertEqual(file.title, "Updated")
        self.assertEqual(file.content_type(), "image/jpeg")

        blobs = file.file
        self.assertEqual(blobs.filename, "test-annexe.jpeg")
        self.assertEqual(blobs.contentType, "image/jpeg")
        self.assertEqual(blobs.size, 103911)

    def test_sync_annexes_publishable_enabled(self):
        self.institution.info_annex_formatting_tal = "python: json['category_title']"
        annexes_json = self.json_annexes_publishable_mock
        self.assertGreater(
            len(annexes_json),
            1,
            "If there are les than 2 annexes in the json, the tes is irrelevant",
        )
        annex = self.item.listFolderContents()[0]
        # delete existing annex and add the new one
        sync_annexes_data(self.item, self.institution, annexes_json)
        self.assertEqual(len(self.item.listFolderContents()), 1)
        annex2 = self.item.listFolderContents()[0]
        self.assertNotEqual(annex.UID(), annex2.UID())

        file = self.item.listFolderContents()[-1]
        self.assertEqual(file.portal_type, "File")
        self.assertEqual(file.id, "annexe")
        self.assertEqual(file.title, "Annexe")
        self.assertEqual(file.content_type(), "image/jpeg")

        blobs = file.file
        self.assertEqual(blobs.filename, "annexe.jpg")
        self.assertEqual(blobs.contentType, "image/jpeg")
        self.assertEqual(blobs.size, 50915)
        # test update
        self.assertEqual(len(self.item.listFolderContents()), 1)
        sync_annexes_data(
            self.item, self.institution, self.json_annexes_publishable_updated_mock
        )
        self.assertEqual(len(self.item.listFolderContents()), 1)
        file = self.item.listFolderContents()[-1]
        self.assertEqual(file.portal_type, "File")
        self.assertEqual(file.id, "annexe")
        self.assertEqual(file.title, "Updated")
        self.assertEqual(file.content_type(), "image/jpeg")

        blobs = file.file
        self.assertEqual(blobs.filename, "annexe.jpg")
        self.assertEqual(blobs.contentType, "image/jpeg")
        self.assertEqual(blobs.size, 50915)

    def test_sync_annex_title_tal_expr(self):
        annexes_json = self.json_annexes_publishable_mock
        sync_annexes_data(self.item, self.institution, annexes_json)
        annex = self.item.listFolderContents()[0]
        # by default annex.title is the annex title...
        self.assertEqual(annex.title, "0s57")
        # use a tal expr
        self.institution.info_annex_formatting_tal = "python: json['category_title']"
        # without force=True, nothing changed
        sync_annexes_data(self.item, self.institution, annexes_json)
        self.assertEqual(annex.title, "0s57")
        sync_annexes_data(self.item, self.institution, annexes_json, force=True)
        self.assertEqual(annex.title, "Annexe")
