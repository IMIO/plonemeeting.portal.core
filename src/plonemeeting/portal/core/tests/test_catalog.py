# -*- coding: utf-8 -*-

from plone import api
from plone.app.testing import applyProfile
from plone.app.testing import login
from plone.app.textfield.value import RichTextValue
from plonemeeting.portal.core.testing import (
    PLONEMEETING_PORTAL_CORE_INTEGRATION_TESTING,
)  # noqa

import unittest


class TestMeetingWorkflow(unittest.TestCase):

    layer = PLONEMEETING_PORTAL_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.catalog = self.portal.portal_catalog
        self.workflow = self.portal.portal_workflow

        self.portal.acl_users._doAddUser("manager", "secret", ["Manager"], [])

        applyProfile(self.portal, "plonemeeting.portal.core:demo")
        login(self.portal, "manager")
        city1 = getattr(self.portal, "amityville")
        brains = api.content.find(context=city1, portal_type="Meeting")
        self.meeting = brains[0].getObject()
        brains = api.content.find(context=self.meeting, portal_type="Item")
        self.meeting_item = brains[0].getObject()

    def testSearchableText(self):
        self.meeting_item.title = "test_title"
        self.meeting_item.deliberation = RichTextValue(
            "test_deliberation", "text/html", "text/html"
        )
        self.meeting_item.reindexObject()
        brain = api.content.find(context=self.meeting, portal_type="Item")[0]
        indexes = self.catalog.getIndexDataForRID(brain.getRID())
        searchable_text = indexes.get("SearchableText")
        self.assertTrue("test_title" in searchable_text)
        self.assertTrue("test_deliberation" in searchable_text)

    def testMeetingValues(self):
        brain = api.content.find(context=self.meeting, portal_type="Item")[0]
        indexes = self.catalog.getIndexDataForRID(brain.getRID())
        self.assertEqual(self.meeting_item.number, indexes.get("item_number"))
        self.assertEqual(self.meeting.title, indexes.get("linkedMeetingTitle"))
        self.assertEqual(self.meeting.UID(), indexes.get("linkedMeetingUID"))
        self.assertEqual(indexes.get("linkedMeetingDate"), 1081567825)
        self.assertEqual(str(self.meeting.date_time.year), indexes.get("year"))

    def testMeetingReviewState(self):
        brain = api.content.find(context=self.meeting, portal_type="Item")[0]
        indexes = self.catalog.getIndexDataForRID(brain.getRID())
        self.assertEqual(
            api.content.get_state(self.meeting), indexes.get("linkedMeetingReviewState")
        )
        self.assertEqual(indexes.get("linkedMeetingReviewState"), "private")
        self.workflow.doActionFor(self.meeting, "send_to_project")
        indexes = self.catalog.getIndexDataForRID(brain.getRID())
        self.assertEqual(
            api.content.get_state(self.meeting), indexes.get("linkedMeetingReviewState")
        )
        self.assertEqual(indexes.get("linkedMeetingReviewState"), "in_project")
        self.workflow.doActionFor(self.meeting, "publish")
        indexes = self.catalog.getIndexDataForRID(brain.getRID())
        self.assertEqual(
            api.content.get_state(self.meeting), indexes.get("linkedMeetingReviewState")
        )
        self.assertEqual(indexes.get("linkedMeetingReviewState"), "published")
