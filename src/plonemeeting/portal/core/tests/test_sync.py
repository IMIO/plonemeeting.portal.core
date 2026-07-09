# -*- coding: utf-8 -*-
from AccessControl import Unauthorized
from datetime import datetime
from imio.helpers.content import object_values
from mockito import mock
from mockito import when
from plone import api
from plone.app.testing import login
from plone.app.testing import logout
from plonemeeting.portal.core.config import API_HEADERS
from plonemeeting.portal.core.content.meeting import IMeeting
from plonemeeting.portal.core.sync_utils import _call_delib_rest_api
from plonemeeting.portal.core.sync_utils import _json_date_to_datetime
from plonemeeting.portal.core.sync_utils import get_formatted_data_from_json
from plonemeeting.portal.core.sync_utils import sync_annexes_data
from plonemeeting.portal.core.sync_utils import sync_items_data
from plonemeeting.portal.core.sync_utils import sync_items_number
from plonemeeting.portal.core.sync_utils import sync_meeting
from plonemeeting.portal.core.sync_utils import sync_meeting_data
from plonemeeting.portal.core.tests.portal_test_case import PmPortalDemoFunctionalTestCase
from unittest.mock import patch

import copy
import json
import os
import pytz
import requests
import transaction


class TestMeetingSynchronization(PmPortalDemoFunctionalTestCase):
    def setUp(self):
        super().setUp()
        with open(os.path.join(os.path.dirname(__file__), "resources/meeting_mock.json")) as json_file:
            self.json_meeting = json.load(json_file)
        with open(os.path.join(os.path.dirname(__file__), "resources/meeting_items_mock.json")) as json_file:
            self.json_meeting_items = json.load(json_file)
        with open(os.path.join(os.path.dirname(__file__), "resources/annexes_not_publishable_mock.json")) as json_file:
            self.json_annexes_not_publishable_mock = json.load(json_file)
        with open(
            os.path.join(
                os.path.dirname(__file__),
                "resources/annexes_not_publishable_updated_mock.json",
            )
        ) as json_file:
            self.json_annexes_not_publishable_updated_mock = json.load(json_file)
        with open(os.path.join(os.path.dirname(__file__), "resources/annexes_publishable_mock.json")) as json_file:
            self.json_annexes_publishable_mock = json.load(json_file)
        with open(
            os.path.join(
                os.path.dirname(__file__),
                "resources/annexes_publishable_updated_mock.json",
            )
        ) as json_file:
            self.json_annexes_publishable_updated_mock = json.load(json_file)
        with open(
            os.path.join(
                os.path.dirname(__file__),
                "resources/preview_import_items_mock.json",
            )
        ) as json_file:
            self.preview_import_items_mock = json.load(json_file)

    def test_sync_meeting_data(self):
        meeting = sync_meeting_data(self.institution, self.json_meeting.get("items")[0])
        self.assertTrue(
            IMeeting.providedBy(meeting),
            "IMeeting not provided by {0}!".format(meeting),
        )
        timezone = api.portal.get_registry_record("plone.portal_timezone")
        self.assertEqual(timezone, "UTC")
        date_time = datetime(2019, 11, 9, 23, 0)
        date_time = date_time.astimezone(pytz.timezone(timezone))
        self.assertEqual(meeting.date_time, date_time)

    def test_sync_meeting_data_stores_meeting_type(self):
        meeting = sync_meeting_data(self.institution, self.json_meeting.get("items")[0])
        self.assertEqual(meeting.meeting_type, self.institution.meeting_type)

    def test_sync_meeting_items(self):
        meeting = sync_meeting_data(self.institution, self.json_meeting.get("items")[0])
        # only a few picked items
        item_external_uids = [
            "ecd55a85b1ee4039bfe22c7c4988876d",
            "12e7d68685074605a2750f0888b0bf52",
            "765ec8ae7ec145b987ab9b21ec45ef14",
            "aa79bc1b61884e289849999c014acc67",
        ]
        json_items = {
            "items": [item for item in self.json_meeting_items.get("items") if item.get("UID") in item_external_uids]
        }
        results = sync_items_data(
            meeting, json_items, self.institution, item_external_uids=item_external_uids + ["fake uid"]
        )
        self.assertEqual(4, results.get("created"))
        self.assertListEqual(item_external_uids, [item.plonemeeting_uid for item in meeting.values()])
        self.login_as_admin()
        api.content.delete(objects=meeting.values())
        self.login_as_decisions_manager()
        # all items
        results = sync_items_data(meeting, self.json_meeting_items, self.institution)
        self.assertEqual(28, results.get("created"))
        self.assertEqual(0, results.get("modified"))
        self.assertEqual(0, results.get("deleted"))
        self.assertEqual(meeting.values()[0].number, "1")
        self.assertEqual(meeting.values()[0].sortable_number, 100)
        self.assertEqual(meeting.values()[0].category, "urbanisme")
        self.assertEqual(meeting.values()[1].number, "2")
        self.assertEqual(meeting.values()[1].sortable_number, 200)
        self.assertEqual(meeting.values()[1].category, "comptabilite")
        self.assertEqual(meeting.values()[10].number, "11")
        self.assertEqual(meeting.values()[10].sortable_number, 1100)
        self.assertEqual(meeting.values()[10].category, "personnel")
        self.assertEqual(meeting.values()[20].number, "21")
        self.assertEqual(meeting.values()[20].sortable_number, 2100)
        self.assertEqual(meeting.values()[20].category, "locations")
        self.assertEqual(meeting.values()[-1].number, "28")
        self.assertEqual(meeting.values()[-1].sortable_number, 2800)
        self.assertEqual(meeting.values()[-1].category, "locations")
        # force re import everything
        self.institution.delib_category_field = "classifier"
        results = sync_items_data(meeting, self.json_meeting_items, self.institution, True)
        self.assertEqual(len(meeting.items()), results.get("modified"))
        self.assertEqual(meeting.values()[0].category, "patrimoine")
        self.assertEqual(meeting.values()[1].category, "finance")
        self.assertEqual(meeting.values()[10].category, "administration")
        self.assertEqual(meeting.values()[20].category, "batiment")
        self.assertEqual(meeting.values()[-1].category, "batiment")

        self.institution.representatives_mappings = None
        sync_items_data(meeting, self.json_meeting_items, self.institution, force=True)

    def test_sync_with_updates_meeting_items(self):
        meeting = sync_meeting_data(self.institution, self.json_meeting.get("items")[0])
        # only a few picked items
        item_external_uids = [
            "ecd55a85b1ee4039bfe22c7c4988876d",
            "12e7d68685074605a2750f0888b0bf52",
            "765ec8ae7ec145b987ab9b21ec45ef14",
            "aa79bc1b61884e289849999c014acc67",
        ]
        json_items = {
            "items": [item for item in self.json_meeting_items.get("items") if item.get("UID") in item_external_uids]
        }
        results = sync_items_data(
            meeting, json_items, self.institution, item_external_uids=item_external_uids + ["fake uid"]
        )
        self.assertEqual(4, results.get("created"))
        self.assertEqual(0, results.get("modified"))
        self.assertEqual(0, results.get("deleted"))

        item_external_uids = [
            "ecd55a85b1ee4039bfe22c7c4988876d",
            "e66269c9342f4e6c861eaff123b20bcb",  # replace
            "765ec8ae7ec145b987ab9b21ec45ef14",
            "aa79bc1b61884e289849999c014acc67",
        ]
        json_items = {
            "items": [item for item in self.json_meeting_items.get("items") if item.get("UID") in item_external_uids]
        }
        decision = {"content-type": "text/html", "data": "<p>Nouvelle décision</p>"}
        modification_date = {"modification_date": "2019-11-26T14:42:40+00:00"}
        json_items.get("items")[0].get("decision").update(decision)
        json_items.get("items")[0].update(modification_date)
        results = sync_items_data(
            meeting, json_items, self.institution, item_external_uids=item_external_uids + ["fake uid"]
        )
        self.assertEqual(1, results.get("created"))
        self.assertEqual(1, results.get("modified"))
        # the item absent from item_external_uids is not deleted but ignored
        self.assertEqual(0, results.get("deleted"))
        self.assertEqual(5, len(meeting.values()))
        # th 4 item in item_external_uids + the ignored one
        self.assertListEqual(
            [
                "ecd55a85b1ee4039bfe22c7c4988876d",
                "12e7d68685074605a2750f0888b0bf52",  # ignored
                "765ec8ae7ec145b987ab9b21ec45ef14",
                "aa79bc1b61884e289849999c014acc67",
                "e66269c9342f4e6c861eaff123b20bcb",
            ],  # added
            [item.plonemeeting_uid for item in meeting.values()],
        )
        # one item in the list is not returned -> deleted
        item_external_uids = [
            "ecd55a85b1ee4039bfe22c7c4988876d",
            "12e7d68685074605a2750f0888b0bf52",  # back but not in json
            "e66269c9342f4e6c861eaff123b20bcb",
            "765ec8ae7ec145b987ab9b21ec45ef14",
            "aa79bc1b61884e289849999c014acc67",
        ]
        results = sync_items_data(
            meeting, json_items, self.institution, item_external_uids=item_external_uids + ["fake uid"]
        )
        self.assertEqual(0, results.get("created"))
        self.assertEqual(0, results.get("modified"))
        # the item present from item_external_uids is not deleted but absent from json is deleted
        self.assertEqual(1, results.get("deleted"))
        self.assertEqual(4, len(meeting.values()))
        self.assertListEqual(
            [
                "ecd55a85b1ee4039bfe22c7c4988876d",
                "765ec8ae7ec145b987ab9b21ec45ef14",
                "aa79bc1b61884e289849999c014acc67",
                "e66269c9342f4e6c861eaff123b20bcb",
            ],
            [item.plonemeeting_uid for item in meeting.values()],
        )
        # all items
        # results {'deleted': 0, 'modified': 0, 'created': 28}
        results = sync_items_data(meeting, self.json_meeting_items, self.institution)
        self.assertEqual(24, results.get("created"))
        self.assertEqual(0, results.get("modified"))
        self.assertEqual(0, results.get("deleted"))
        decision = {"content-type": "text/html", "data": "<p>Nouvelle décision</p>"}
        modification_date = {"modification_date": "2019-11-26T14:43:40+00:00"}
        self.json_meeting_items.get("items")[0].get("decision").update(decision)
        self.json_meeting_items.get("items")[0].update(modification_date)
        results = sync_items_data(meeting, self.json_meeting_items, self.institution)
        self.assertEqual(results.get("created"), 0)
        self.assertEqual(results.get("modified"), 1)
        self.assertEqual(results.get("deleted"), 0)
        self.json_meeting_items.get("items")[0]["itemNumber"] = 110
        results = sync_items_data(meeting, self.json_meeting_items, self.institution)
        self.assertEqual(results.get("created"), 0)
        self.assertEqual(results.get("modified"), 1)
        self.assertEqual(results.get("deleted"), 0)

    def test_sync_no_modif_date_no_update(self):
        meeting = sync_meeting_data(self.institution, self.json_meeting.get("items")[0])
        results = sync_items_data(meeting, self.json_meeting_items, self.institution)
        decision = {"content-type": "text/html", "data": "<p>Nouvelle décision</p>"}
        self.json_meeting_items.get("items")[0].get("decision").update(decision)
        results = sync_items_data(meeting, self.json_meeting_items, self.institution)
        self.assertEqual(results.get("created"), 0)
        self.assertEqual(results.get("modified"), 0)
        self.assertEqual(results.get("deleted"), 0)
        self.json_meeting_items.get("items")[0]["formatted_itemNumber"] = "1.1"
        results = sync_items_data(meeting, self.json_meeting_items, self.institution)
        self.assertEqual(results.get("created"), 0)
        self.assertEqual(results.get("modified"), 0)
        self.assertEqual(results.get("deleted"), 0)

    def test_force_sync_item(self):
        meeting = sync_meeting_data(self.institution, self.json_meeting.get("items")[0])
        results = sync_items_data(meeting, self.json_meeting_items, self.institution, force=True)
        decision = {"content-type": "text/html", "data": "<p>Nouvelle décision</p>"}
        self.json_meeting_items.get("items")[0].get("decision").update(decision)
        results = sync_items_data(meeting, self.json_meeting_items, self.institution, force=True)
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
            get_formatted_data_from_json("python: json['decision']['data']", self.item, item_json),
            item_jsons[0]["decision"]["data"],
        )
        item_json = item_jsons[1]
        self.assertEqual(
            get_formatted_data_from_json(
                "python: '{}<p>DECIDE</p>{}'.format(" "json['motivation']['data'], json['decision']['data'])",
                self.item,
                item_json,
            ),
            "{}<p>DECIDE</p>{}".format(item_json["motivation"]["data"], item_json["decision"]["data"]),
        )

    def test_sync_annexes_publishable_enabled(self):
        self.institution.info_annex_formatting_tal = "python: json['category_title']"
        annexes_json = self.json_annexes_publishable_mock
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
        sync_annexes_data(self.item, self.institution, self.json_annexes_publishable_updated_mock)
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

    def test_sync_not_mapped_groups_in_charge_are_ignored(self):
        self.institution.representatives_mappings = [
            {
                "representative_key": "dummy_mapped_uid_1",
                "representative_value": "Mr. Mapped One",
                "representative_long_value": "Mister Mapped One",
                "active": True,
            },
            {
                "representative_key": "dummy_mapped_uid_2",
                "representative_value": "Mr Mapped Two",
                "representative_long_value": "Mister Mapped Two",
                "active": True,
            },
        ]

        meeting = sync_meeting_data(self.institution, self.json_meeting.get("items")[0])
        sync_items_data(meeting, self.json_meeting_items, self.institution)

        self.assertEqual(["dummy_mapped_uid_1", "dummy_mapped_uid_2"], meeting.values()[0].representatives_in_charge)
        self.assertEqual(
            ["dummy_mapped_uid_1", "dummy_mapped_uid_2"], meeting.values()[0].long_representatives_in_charge
        )
        self.assertEqual(["dummy_mapped_uid_1"], meeting.values()[1].representatives_in_charge)
        self.assertEqual(["dummy_mapped_uid_1"], meeting.values()[1].long_representatives_in_charge)
        self.assertEqual([], meeting.values()[2].representatives_in_charge)
        self.assertEqual([], meeting.values()[2].long_representatives_in_charge)
        #  Check if order from PM is preserved
        self.assertEqual(["dummy_mapped_uid_2", "dummy_mapped_uid_1"], meeting.values()[3].representatives_in_charge)
        self.assertEqual(
            ["dummy_mapped_uid_2", "dummy_mapped_uid_1"], meeting.values()[3].long_representatives_in_charge
        )

    def test_item_title_formatting_tal(self):
        self.institution.item_title_formatting_tal = "python: '<h2>' + json['title'] + '</h2>'"
        meeting = sync_meeting_data(self.institution, self.json_meeting.get("items")[0])
        sync_items_data(meeting, self.json_meeting_items, self.institution)
        self.assertEqual(meeting.values()[0].formatted_title.raw, "<h2>" + meeting.values()[0].title + "</h2>")

    def test_empty_item_title_formatting_tal(self):
        meeting = sync_meeting_data(self.institution, self.json_meeting.get("items")[0])
        sync_items_data(meeting, self.json_meeting_items, self.institution)
        self.assertIsNotNone(meeting.values()[0].formatted_title)
        self.assertEqual(meeting.values()[0].formatted_title.raw, "<p>" + meeting.values()[0].title + "</p>")

    def test_item_view(self):
        meeting = sync_meeting_data(self.institution, self.json_meeting.get("items")[0])
        sync_items_data(meeting, self.json_meeting_items, self.institution)
        item = object_values(meeting, "Item")[0]
        item_view = item.restrictedTraverse("@@view")
        self.assertTrue(item_view())

    def test_sync_items_number(self):
        changes = {}
        for item in self.meeting.listFolderContents():
            changes[item.UID()] = {"sortable_number": item.sortable_number, "number": item.number}

        self.assertEqual(0, sync_items_number({}))
        self.assertEqual(0, sync_items_number(changes))

        for item in self.meeting.listFolderContents():
            changes[item.UID()] = {"sortable_number": item.sortable_number, "number": "random fake news"}
        self.assertEqual(0, sync_items_number(changes))

        counter = 500
        for item in self.meeting.listFolderContents():
            changes[item.UID()] = {"sortable_number": counter, "number": "random fake news"}
            counter += 5000
        self.assertEqual(3, sync_items_number(changes))

        changes[list(changes.keys())[0]]["sortable_number"] = 100
        self.assertEqual(1, sync_items_number(changes))

        items = self.meeting.listFolderContents()
        items_brains = api.content.find(context=self.meeting, portal_type="Item", linkedMeetingUID=self.meeting.UID())
        self.assertEqual(100, items[0].sortable_number)
        self.assertEqual(100, items_brains[0].sortable_number)
        self.assertEqual("random fake news", items[0].number)
        self.assertEqual("random fake news", items_brains[0].number)
        self.assertEqual(5500, items[1].sortable_number)
        self.assertEqual(5500, items_brains[1].sortable_number)
        self.assertEqual("random fake news", items[0].number)
        self.assertEqual("random fake news", items_brains[0].number)
        self.assertEqual(10500, items[2].sortable_number)
        self.assertEqual(10500, items_brains[2].sortable_number)
        self.assertEqual("random fake news", items[0].number)
        self.assertEqual("random fake news", items_brains[0].number)

    def test_response_is_not_200(self):
        when(requests).get(
            "fake_url", auth=(self.institution.username, self.institution.password), headers=API_HEADERS
        ).thenReturn(mock({"status_code": 500}))

        with self.assertRaises(ValueError) as ws_err:
            _call_delib_rest_api("fake_url", self.institution)
        self.assertEqual("Web service connection error !", str(ws_err.exception))

    def test_raises_when_encountered_not_publishable_annexes(self):
        self.institution.info_annex_formatting_tal = "python: json['category_title']"
        annexes_not_publishable_but_published = copy.deepcopy(self.json_annexes_publishable_mock)
        annexes_not_publishable_but_published[0]["publishable"] = False
        with self.assertRaises(ValueError):
            sync_annexes_data(self.item, self.institution, annexes_not_publishable_but_published)

        annexes_not_publishable_but_published[0]["publishable"] = True
        sync_annexes_data(self.item, self.institution, annexes_not_publishable_but_published)

        del annexes_not_publishable_but_published[0]["publishable"]
        with self.assertRaises(ValueError):
            sync_annexes_data(self.item, self.institution, annexes_not_publishable_but_published)

    @patch("plonemeeting.portal.core.browser.sync._fetch_preview_items")
    def test_pre_import_view(self, _fetch_preview_items):
        meeting = self.json_meeting
        self.portal.REQUEST.form["external_meeting_uid"] = meeting.get("UID")
        _fetch_preview_items.return_value = self.preview_import_items_mock

        decisions = self.institution.decisions
        pre_import_view = decisions.restrictedTraverse("@@pre_import_report_form")

        self.assertTrue(pre_import_view())  # This should render with no exception

        logout()  # Anonymous may not access this form
        with self.assertRaises(Unauthorized):
            decisions.restrictedTraverse("@@pre_import_report_form")

        # Foreign institution decisions manager may not access this form either
        login(self.portal, "belleville-decisions-manager")
        with self.assertRaises(Unauthorized):
            decisions.restrictedTraverse("@@pre_import_report_form")

    @patch("plonemeeting.portal.core.browser.sync._fetch_preview_items")
    def test_pre_sync_view(self, _fetch_preview_items):
        _fetch_preview_items.return_value = self.preview_import_items_mock

        meeting = sync_meeting_data(self.institution, self.json_meeting.get("items")[0])
        pre_sync_view = meeting.restrictedTraverse("@@pre_sync_report_form")

        self.assertTrue(pre_sync_view())  # This should render with no exception

        logout()  # Anonymous may not access this form
        with self.assertRaises(Unauthorized):
            meeting.restrictedTraverse("@@pre_sync_report_form")

        # Foreign institution decisions manager may not access this form either
        login(self.portal, "belleville-decisions-manager")
        with self.assertRaises(Unauthorized):
            meeting.restrictedTraverse("@@pre_sync_report_form")

    @patch("plonemeeting.portal.core.browser.sync._fetch_preview_items")
    def test_pre_sync_view_remove(self, _fetch_preview_items):
        _fetch_preview_items.return_value = self.preview_import_items_mock
        login(self.portal, "manager")
        meeting = sync_meeting_data(self.institution, self.json_meeting.get("items")[0])
        pre_sync_view = meeting.restrictedTraverse("@@pre_sync_report_form")
        pre_sync_view.institution = self.institution

        # Try to remove an item with the manager account
        api.content.create(
            meeting, "Item", id="toto", title="Toto", plonemeeting_uid=self.preview_import_items_mock["items"][0]["UID"]
        )
        self.assertEqual(len(meeting.items()), 1)
        self.portal.REQUEST.form["item_uid__" + self.preview_import_items_mock["items"][0]["UID"]] = True
        self.portal.REQUEST.form["form.buttons.remove"] = True
        pre_sync_view.handle_remove(pre_sync_view, "remove")
        self.assertEqual(len(meeting.items()), 0)

        # Then with belleville-decisions-manager
        api.content.create(
            meeting, "Item", id="toto", title="Toto", plonemeeting_uid=self.preview_import_items_mock["items"][0]["UID"]
        )
        login(self.portal, "belleville-decisions-manager")
        self.assertEqual(len(meeting.items()), 1)

        self.portal.REQUEST.form["item_uid__" + self.preview_import_items_mock["items"][0]["UID"]] = True
        self.portal.REQUEST.form["form.buttons.remove"] = True
        pre_sync_view.handle_remove(pre_sync_view, "remove")
        self.assertEqual(len(meeting.items()), 0)

        # Let's try with an anonymous user
        login(self.portal, "manager")
        api.content.create(
            meeting, "Item", id="toto", title="Toto", plonemeeting_uid=self.preview_import_items_mock["items"][0]["UID"]
        )
        api.content.transition(meeting, "send_to_project")
        logout()
        self.assertEqual(len(meeting.items()), 1)
        with self.assertRaises(Unauthorized):
            pre_sync_view = meeting.restrictedTraverse("@@pre_sync_report_form")
            self.portal.REQUEST.form["item_uid__" + self.preview_import_items_mock["items"][0]["UID"]] = True
            self.portal.REQUEST.form["form.buttons.remove"] = True
            pre_sync_view.handle_remove(pre_sync_view, "remove")
        self.assertEqual(len(meeting.items()), 1)

        # Finally when a meeting is accepted (you can't)
        login(self.portal, "manager")
        api.content.transition(meeting, "publish")
        login(self.portal, "belleville-decisions-manager")
        self.assertEqual(len(meeting.items()), 1)
        self.portal.REQUEST.form["item_uid__" + self.preview_import_items_mock["items"][0]["UID"]] = True
        self.portal.REQUEST.form["form.buttons.remove"] = True
        pre_sync_view.handle_remove(pre_sync_view, "remove")
        self.assertEqual(len(meeting.items()), 1)
        self.assertIn("statusmessages", self.portal.REQUEST.response.cookies.keys())

    def test_import_meeting_form_handle_select_redirects(self):
        login(self.portal, "manager")
        form = self.institution.decisions.restrictedTraverse("@@import_meeting")
        with patch.object(form, "extractData", return_value=({"meeting": "EXT-UID"}, [])):
            form.handle_select(form, None)
        self.assertEqual(self.portal.REQUEST.response.status, 302)
        self.assertEqual(
            self.portal.REQUEST.response.headers["location"],
            self.institution.decisions.absolute_url()
            + "/@@pre_import_report_form?external_meeting_uid=EXT-UID",
        )

    def test_import_meeting_form_handle_select_with_errors(self):
        login(self.portal, "manager")
        form = self.institution.decisions.restrictedTraverse("@@import_meeting")
        with patch.object(form, "extractData", return_value=({}, ["error"])):
            form.handle_select(form, None)
        self.assertEqual(form.status, form.formErrorsMessage)

    def test_import_meeting_form_handle_cancel_redirects(self):
        login(self.portal, "manager")
        form = self.institution.decisions.restrictedTraverse("@@import_meeting")
        form.handle_cancel(form, None)
        self.assertEqual(self.portal.REQUEST.response.status, 302)
        self.assertEqual(
            self.portal.REQUEST.response.headers["location"],
            self.institution.decisions.absolute_url(),
        )

    def test_import_meeting_form_update_handles_connection_error(self):
        login(self.portal, "manager")
        form = self.institution.decisions.restrictedTraverse("@@import_meeting")
        # Make the underlying super().update() raise — this exercises the
        # try/except wrapper and the _notify_error_and_cancel → handle_cancel chain.
        from plone.autoform.form import AutoExtensibleForm
        with patch.object(
            AutoExtensibleForm, "update", side_effect=requests.exceptions.ConnectionError("boom")
        ):
            form.update()
        self.assertEqual(self.portal.REQUEST.response.status, 302)
        self.assertEqual(
            self.portal.REQUEST.response.headers["location"],
            self.institution.decisions.absolute_url(),
        )

    @patch("plonemeeting.portal.core.browser.sync._sync_meeting")
    def test_pre_sync_handle_sync_calls_sync_meeting(self, _sync_meeting):
        login(self.portal, "manager")
        meeting = sync_meeting_data(self.institution, self.json_meeting.get("items")[0])
        pre_sync_view = meeting.restrictedTraverse("@@pre_sync_report_form")
        pre_sync_view.institution = self.institution
        pre_sync_view.external_meeting_uid = "EXT-UID"

        self.portal.REQUEST.form["item_uid__abc"] = True
        self.portal.REQUEST.form["item_uid__def"] = True
        pre_sync_view.handle_sync(pre_sync_view, "sync")

        _sync_meeting.assert_called_once()
        kwargs = _sync_meeting.call_args.kwargs
        self.assertCountEqual(kwargs["item_external_uids"], ["abc", "def"])

    def test_pre_sync_handle_cancel_redirects(self):
        login(self.portal, "manager")
        meeting = sync_meeting_data(self.institution, self.json_meeting.get("items")[0])
        pre_sync_view = meeting.restrictedTraverse("@@pre_sync_report_form")
        pre_sync_view.institution = self.institution

        pre_sync_view.handle_cancel(pre_sync_view, None)
        self.assertEqual(self.portal.REQUEST.response.status, 302)
        self.assertEqual(
            self.portal.REQUEST.response.headers["location"],
            f"{self.institution.absolute_url()}/decisions/#seance={meeting.UID()}",
        )

    @patch("plonemeeting.portal.core.browser.sync._sync_meeting")
    def test_pre_import_handle_import_calls_sync_meeting(self, _sync_meeting):
        login(self.portal, "manager")
        decisions = self.institution.decisions
        pre_import_view = decisions.restrictedTraverse("@@pre_import_report_form")
        pre_import_view.institution = self.institution
        pre_import_view.external_meeting_uid = "EXT-UID"

        self.portal.REQUEST.form["item_uid__abc"] = True
        self.portal.REQUEST.form["item_uid__def"] = True
        pre_import_view.handle_import(pre_import_view, "import")

        _sync_meeting.assert_called_once()
        kwargs = _sync_meeting.call_args.kwargs
        self.assertCountEqual(kwargs["item_external_uids"], ["abc", "def"])

    def test_pre_import_handle_cancel_redirects(self):
        login(self.portal, "manager")
        decisions = self.institution.decisions
        pre_import_view = decisions.restrictedTraverse("@@pre_import_report_form")

        pre_import_view.handle_cancel(pre_import_view, None)
        self.assertEqual(self.portal.REQUEST.response.status, 302)
        self.assertEqual(
            self.portal.REQUEST.response.headers["location"],
            decisions.absolute_url() + "/@@import_meeting",
        )

    @patch("plonemeeting.portal.core.sync_utils._call_delib_rest_api")
    def test_sync_meeting(self, _call_api):
        login(self.portal, "manager")
        meeting_response = mock({"text": json.dumps(self.json_meeting)})
        items_response = mock({"text": json.dumps(self.json_meeting_items)})
        _call_api.side_effect = [meeting_response, items_response]

        meeting_external_uid = self.json_meeting["items"][0]["UID"]
        status, uid = sync_meeting(self.institution, meeting_external_uid, with_annexes=False)

        self.assertEqual(_call_api.call_count, 2)
        self.assertIsNotNone(uid)
        self.assertIn("Meeting imported", status)
        # The meeting now exists under the institution's decisions folder.
        brains = api.content.find(
            context=self.institution.decisions, plonemeeting_uid=meeting_external_uid
        )
        self.assertEqual(len(brains), 1)

    @patch("plonemeeting.portal.core.sync_utils._call_delib_rest_api")
    def test_sync_meeting_unexpected_count(self, _call_api):
        login(self.portal, "manager")
        bogus_payload = copy.deepcopy(self.json_meeting)
        bogus_payload["items_total"] = 0
        _call_api.return_value = mock({"text": json.dumps(bogus_payload)})

        with self.assertRaises(ValueError):
            sync_meeting(self.institution, "anything")

    # --- _reconcile_items / _reconcile_annexes helpers and tests ----------
    # Inputs are constructed inline so each scenario stays explicit; the
    # reconcile methods are pure functions of (api payload, local content)
    # so no REST mocking is needed here.

    def _make_reconcile_view(self):
        login(self.portal, "manager")
        meeting = api.content.create(
            container=self.institution.decisions,
            type="Meeting",
            id="reconcile-meeting",
            title="Reconcile Meeting",
        )
        view = meeting.restrictedTraverse("@@pre_sync_report_form")
        view.institution = self.institution
        return meeting, view

    @staticmethod
    def _make_local_item(meeting, uid, modified_iso, number, item_id=None, with_annex_titles=()):
        item = api.content.create(
            container=meeting,
            type="Item",
            id=item_id or "item-" + uid,
            title="Local " + uid,
            plonemeeting_uid=uid,
        )
        item.plonemeeting_last_modified = _json_date_to_datetime(modified_iso)
        item.number = number
        for title in with_annex_titles:
            api.content.create(container=item, type="File", id=title, title=title)
        return item

    @staticmethod
    def _api_item(uid, modified_iso, number, annexes=()):
        return {
            "UID": uid,
            "modified": modified_iso,
            "formatted_itemNumber": number,
            "category": {"title": "cat"},
            "classifier": {"title": "cls"},
            "representatives_in_charge": "-",
            "extra_include_annexes": list(annexes),
        }

    @staticmethod
    def _index_by_uid(reconciled):
        return {item["UID"]: item for item in reconciled["items"]}

    def test_reconcile_items_unchanged(self):
        meeting, view = self._make_reconcile_view()
        modified = "2024-01-01T10:00:00+00:00"
        self._make_local_item(meeting, "uid-1", modified, "1")
        api_items = {"items": [self._api_item("uid-1", modified, "1")]}

        reconciled = view._reconcile_items(api_items, list(meeting.objectValues()))

        item = self._index_by_uid(reconciled)["uid-1"]
        self.assertEqual(item["status"], "unchanged")
        self.assertEqual(item["annexes_status"], {})

    def test_reconcile_items_modified_when_date_differs(self):
        meeting, view = self._make_reconcile_view()
        local_modified = "2024-01-01T10:00:00+00:00"
        api_modified = "2024-02-01T10:00:00+00:00"
        self._make_local_item(meeting, "uid-1", local_modified, "1")
        api_items = {"items": [self._api_item("uid-1", api_modified, "1")]}

        reconciled = view._reconcile_items(api_items, list(meeting.objectValues()))

        item = self._index_by_uid(reconciled)["uid-1"]
        self.assertEqual(item["status"], "modified")

    def test_reconcile_items_modified_when_number_differs(self):
        meeting, view = self._make_reconcile_view()
        modified = "2024-01-01T10:00:00+00:00"
        self._make_local_item(meeting, "uid-1", modified, "1")
        api_items = {"items": [self._api_item("uid-1", modified, "2")]}

        reconciled = view._reconcile_items(api_items, list(meeting.objectValues()))

        item = self._index_by_uid(reconciled)["uid-1"]
        self.assertEqual(item["status"], "modified")

    def test_reconcile_items_added_with_and_without_annexes(self):
        _meeting, view = self._make_reconcile_view()
        api_items = {
            "items": [
                self._api_item("uid-new-no-annex", "2024-03-01T10:00:00+00:00", "1"),
                self._api_item(
                    "uid-new-with-annex",
                    "2024-03-01T10:00:00+00:00",
                    "2",
                    annexes=[
                        {"UID": "a1", "title": "annex one", "modified": "2024-03-01T10:00:00+00:00"},
                        {"UID": "a2", "title": "annex two", "modified": "2024-03-01T10:00:00+00:00"},
                    ],
                ),
            ],
        }

        reconciled = view._reconcile_items(api_items, [])
        by_uid = self._index_by_uid(reconciled)

        no_annex = by_uid["uid-new-no-annex"]
        self.assertEqual(no_annex["status"], "added")
        self.assertEqual(no_annex["local_last_modified"], "-")
        self.assertEqual(no_annex["annexes_status"], {})

        with_annex = by_uid["uid-new-with-annex"]
        self.assertEqual(with_annex["status"], "added")
        self.assertEqual(with_annex["annexes_status"]["added"]["count"], 2)
        self.assertEqual(
            with_annex["annexes_status"]["added"]["titles"],
            ["annex one", "annex two"],
        )

    def test_reconcile_items_removed_with_and_without_annexes(self):
        meeting, view = self._make_reconcile_view()
        modified = "2024-01-01T10:00:00+00:00"
        self._make_local_item(meeting, "uid-gone-empty", modified, "9", item_id="gone-empty")
        self._make_local_item(
            meeting,
            "uid-gone-with-annex",
            modified,
            "10",
            item_id="gone-with-annex",
            with_annex_titles=("annex-x", "annex-y"),
        )

        reconciled = view._reconcile_items({"items": []}, list(meeting.objectValues()))
        by_uid = self._index_by_uid(reconciled)

        empty = by_uid["uid-gone-empty"]
        self.assertEqual(empty["status"], "removed")
        self.assertEqual(empty["annexes_status"], {})

        with_annex = by_uid["uid-gone-with-annex"]
        self.assertEqual(with_annex["status"], "removed")
        self.assertEqual(with_annex["annexes_status"]["removed"]["count"], 2)
        self.assertEqual(
            sorted(with_annex["annexes_status"]["removed"]["titles"]),
            ["annex-x", "annex-y"],
        )

    def test_reconcile_annexes_all_statuses(self):
        meeting, view = self._make_reconcile_view()
        modified = "2024-01-01T10:00:00+00:00"
        local_item = self._make_local_item(meeting, "uid-1", modified, "1")
        # Three local annexes: one will match unchanged, one modified, one removed.
        unchanged_annex = api.content.create(
            container=local_item, type="File", id="a-unchanged", title="Unchanged annex"
        )
        unchanged_annex.plonemeeting_uid = "annex-unchanged"
        unchanged_annex.plonemeeting_last_modified = _json_date_to_datetime(modified)

        modified_annex = api.content.create(
            container=local_item, type="File", id="a-modified", title="Modified annex"
        )
        modified_annex.plonemeeting_uid = "annex-modified"
        modified_annex.plonemeeting_last_modified = _json_date_to_datetime(modified)

        removed_annex = api.content.create(
            container=local_item, type="File", id="a-removed", title="Removed annex"
        )
        removed_annex.plonemeeting_uid = "annex-removed"
        removed_annex.plonemeeting_last_modified = _json_date_to_datetime(modified)

        api_annexes = [
            {"UID": "annex-unchanged", "title": "Unchanged annex", "modified": modified},
            {"UID": "annex-modified", "title": "Modified annex",
             "modified": "2024-06-01T10:00:00+00:00"},
            {"UID": "annex-added", "title": "Added annex", "modified": modified},
        ]

        result = view._reconcile_annexes(api_annexes, local_item.objectValues())

        self.assertEqual(set(result.keys()), {"added", "unchanged", "modified", "removed"})
        self.assertEqual(result["added"]["count"], 1)
        self.assertEqual(result["added"]["titles"], ["Added annex"])
        self.assertEqual(result["unchanged"]["count"], 1)
        self.assertEqual(result["unchanged"]["titles"], ["Unchanged annex"])
        self.assertEqual(result["modified"]["count"], 1)
        self.assertEqual(result["modified"]["titles"], ["Modified annex"])
        self.assertEqual(result["removed"]["count"], 1)
        self.assertEqual(result["removed"]["titles"], ["Removed annex"])

    def test_reconcile_annexes_strips_empty_buckets(self):
        meeting, view = self._make_reconcile_view()
        modified = "2024-01-01T10:00:00+00:00"
        local_item = self._make_local_item(meeting, "uid-1", modified, "1")
        annex = api.content.create(
            container=local_item, type="File", id="a-unchanged", title="Annex"
        )
        annex.plonemeeting_uid = "annex-unchanged"
        annex.plonemeeting_last_modified = _json_date_to_datetime(modified)

        api_annexes = [
            {"UID": "annex-unchanged", "title": "Annex", "modified": modified},
        ]

        result = view._reconcile_annexes(api_annexes, local_item.objectValues())

        self.assertEqual(set(result.keys()), {"unchanged"})
        self.assertEqual(result["unchanged"]["count"], 1)
