# -*- coding: utf-8 -*-

from datetime import datetime
from imio.helpers.content import richtextval
from plone import api
from plonemeeting.portal.core.tests.portal_test_case import PmPortalDemoFunctionalTestCase
from Products.PluginIndexes.DateIndex.DateIndex import DateIndex


class TestMeetingWorkflow(PmPortalDemoFunctionalTestCase):
    def setUp(self):
        super().setUp()
        self.login_as_admin()

    def testSearchableText(self):
        self.item.formatted_title = richtextval("<p>test_title</p>")
        self.item.decision = richtextval("<p>test_decision</p>")
        self.item.reindexObject()
        brain = api.content.find(context=self.meeting, portal_type="Item")[0]
        indexes = self.catalog.getIndexDataForRID(brain.getRID())
        searchable_text = indexes.get("SearchableText")
        self.assertIn("test_title", searchable_text)
        self.assertIn("test_decision", searchable_text)

    def testMeetingValues(self):
        brain = api.content.find(context=self.meeting, portal_type="Item")[0]
        indexes = self.catalog.getIndexDataForRID(brain.getRID())
        # indexed item number is a sortable integer
        self.assertEqual(self.item.number, "1")
        self.assertEqual(self.item.sortable_number, 100)
        self.assertEqual(indexes.get("sortable_number"), 100)
        self.assertEqual(indexes.get("number"), "1")
        self.assertEqual(self.meeting.title, indexes.get("linkedMeetingTitle"))
        self.assertEqual(self.meeting.UID(), indexes.get("linkedMeetingUID"))
        self.assertEqual(
            indexes.get("linkedMeetingDate"),
            DateIndex("test")._convert(datetime(2018, 12, 20, 18, 25, 43, 51100)),
        )
        self.assertEqual(str(self.meeting.date_time.year), indexes.get("year"))

    def testMeetingReviewState(self):
        brain = api.content.find(context=self.meeting, portal_type="Item")[0]
        indexes = self.catalog.getIndexDataForRID(brain.getRID())
        self.assertEqual(
            api.content.get_state(self.meeting), indexes.get("linkedMeetingReviewState")
        )
        self.assertEqual(indexes.get("linkedMeetingReviewState"), "decision")
        self.workflow.doActionFor(self.meeting, "back_to_project")
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
        self.assertEqual(indexes.get("linkedMeetingReviewState"), "decision")
