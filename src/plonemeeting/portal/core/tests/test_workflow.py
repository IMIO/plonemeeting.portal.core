# -*- coding: utf-8 -*-
from plone import api
from plone.app.testing import login
from plone.app.testing import logout
from plonemeeting.portal.core.testing import (
    PLONEMEETING_PORTAL_DEMO_FUNCTIONAL_TESTING,
)  # noqa
from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CMFCore.utils import _checkPermission as checkPerm
from Products.CMFCore.permissions import AccessContentsInformation
from Products.CMFCore.permissions import AddPortalContent
from Products.CMFCore.permissions import View
from Products.CMFCore.permissions import ModifyPortalContent

import unittest


WF = "meeting_workflow"


class TestMeetingWorkflow(unittest.TestCase):

    layer = PLONEMEETING_PORTAL_DEMO_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.catalog = self.portal.portal_catalog
        self.workflow = self.portal.portal_workflow

        self.portal.acl_users._doAddUser("member", "secret", ["Member"], [])
        self.portal.acl_users._doAddUser("reviewer", "secret", ["Reviewer"], [])
        self.portal.acl_users._doAddUser("manager", "secret", ["Manager"], [])
        self.portal.acl_users._doAddUser("editor", " secret", ["Editor"], [])
        self.portal.acl_users._doAddUser("reader", "secret", ["Reader"], [])

        login(self.portal, "manager")
        self.city1 = getattr(self.portal, "amityville")
        self.meeting = api.content.create(
            container=self.city1, title="My meeting", type="Meeting"
        )
        self.meeting_item = api.content.create(
            container=self.meeting, title="My item", type="Item"
        )

        self.portal.acl_users._doAddUser(
            "institution_manager",
            "secret",
            [],
            [],
            groups=["amityville-institution_managers"],
        )

    def tearDown(self):
        login(self.portal, "manager")
        api.content.delete(obj=self.meeting)
        logout()

    def _check_index(self, obj, index_name, expected_value):
        brain = api.content.find(UID=obj.UID())[0]
        indexes = self.catalog.getIndexDataForRID(brain.getRID())
        indexed_value = indexes.get(index_name, None)
        self.assertEqual(
            indexed_value,
            expected_value,
            "Object {0} should have indexed value {1} for {2} but has {3}".format(
                obj, expected_value, index_name, indexed_value
            ),
        )

    def _check_state(self, obj, expected_review_state):
        current_state = self.workflow.getInfoFor(obj, "review_state")
        self.assertEqual(
            current_state,
            expected_review_state,
            "Object {0} should have review state {1} but has {2}".format(
                obj, expected_review_state, current_state
            ),
        )

    def testReviewStateIndexing(self):
        self._check_index(self.meeting_item, "linkedMeetingReviewState", "private")
        self.workflow.doActionFor(self.meeting, "send_to_project")
        self._check_index(self.meeting_item, "linkedMeetingReviewState", "in_project")
        self.workflow.doActionFor(self.meeting, "publish")
        self._check_index(self.meeting_item, "linkedMeetingReviewState", "decision")

    def testOwnerSubmitAPrivateMeetingAndRetract(self):
        self._check_state(self.meeting, "private")
        self.workflow.doActionFor(self.meeting, "send_to_project")
        self._check_state(self.meeting, "in_project")
        self.workflow.doActionFor(self.meeting, "back_to_private")
        self._check_state(self.meeting, "private")

    def testOwnerCannotChangeWorkflow(self):
        login(self.portal, "member")
        self._check_state(self.meeting, "private")
        self.assertRaises(
            WorkflowException,
            self.workflow.doActionFor,
            self.meeting,
            "send_to_project",
        )

    def testViewIsNotAcquiredInPrivateState(self):
        self.assertEqual(self.meeting.acquiredRolesAreUsedBy(View), "")  # not checked

    def testViewPrivateMeeting(self):
        self._check_state(self.meeting, "private")
        # Owner is allowed
        login(self.portal, "manager")
        self.assertTrue(checkPerm(View, self.meeting))
        self.assertTrue(checkPerm(View, self.meeting_item))
        # Member is denied
        login(self.portal, "member")
        self.assertFalse(checkPerm(View, self.meeting))
        self.assertFalse(checkPerm(View, self.meeting_item))
        # Reviewer is denied
        login(self.portal, "reviewer")
        self.assertFalse(checkPerm(View, self.meeting))
        self.assertFalse(checkPerm(View, self.meeting_item))
        # Anonymous is denied
        logout()
        self.assertFalse(checkPerm(View, self.meeting))
        self.assertFalse(checkPerm(View, self.meeting_item))
        # Editor is allowed
        login(self.portal, "editor")
        self.assertTrue(checkPerm(View, self.meeting))
        self.assertTrue(checkPerm(View, self.meeting_item))
        # Reader is allowed
        login(self.portal, "reader")
        self.assertTrue(checkPerm(View, self.meeting))
        self.assertTrue(checkPerm(View, self.meeting_item))
        # Institution Manager is allowed
        login(self.portal, "institution_manager")
        self.assertTrue(checkPerm(View, self.meeting))
        self.assertTrue(checkPerm(View, self.meeting_item))

    def testViewIsNotAcquiredInPublishedStates(self):
        # transition requires Review portal content
        login(self.portal, "manager")
        self.workflow.doActionFor(self.meeting, "send_to_project")
        self.assertEqual(self.meeting.acquiredRolesAreUsedBy(View), "")  # not checked
        self.workflow.doActionFor(self.meeting, "publish")
        self.assertEqual(self.meeting.acquiredRolesAreUsedBy(View), "")  # not checked

    def testViewInProjectMeeting(self):
        # transition requires Review portal content
        login(self.portal, "manager")
        self.workflow.doActionFor(self.meeting, "send_to_project")
        # Owner is allowed
        self.assertTrue(checkPerm(View, self.meeting))
        self.assertTrue(checkPerm(View, self.meeting_item))
        # Member is allowed
        login(self.portal, "member")
        self.assertTrue(checkPerm(View, self.meeting))
        self.assertTrue(checkPerm(View, self.meeting_item))
        # Reviewer is denied  but he acquires through Anonymous Role
        login(self.portal, "reviewer")
        self.assertTrue(checkPerm(View, self.meeting))
        self.assertTrue(checkPerm(View, self.meeting_item))
        # Anonymous is allowed
        logout()
        self.assertTrue(checkPerm(View, self.meeting))
        self.assertTrue(checkPerm(View, self.meeting_item))
        # Editor is allowed
        login(self.portal, "editor")
        self.assertTrue(checkPerm(View, self.meeting))
        self.assertTrue(checkPerm(View, self.meeting_item))
        # Reader is allowed
        login(self.portal, "reader")
        self.assertTrue(checkPerm(View, self.meeting))
        self.assertTrue(checkPerm(View, self.meeting_item))
        # Institution Manager is allowed
        login(self.portal, "institution_manager")
        self.assertTrue(checkPerm(View, self.meeting))
        self.assertTrue(checkPerm(View, self.meeting_item))

    def testViewPublishedMeeting(self):
        # transition requires Review portal content
        login(self.portal, "manager")
        self.workflow.doActionFor(self.meeting, "send_to_project")
        self.workflow.doActionFor(self.meeting, "publish")
        # Owner is allowed
        self.assertTrue(checkPerm(View, self.meeting))
        self.assertTrue(checkPerm(View, self.meeting_item))
        # Member is allowed
        login(self.portal, "member")
        self.assertTrue(checkPerm(View, self.meeting))
        self.assertTrue(checkPerm(View, self.meeting_item))
        # Reviewer is denied  but he acquires through Anonymous Role
        login(self.portal, "reviewer")
        self.assertTrue(checkPerm(View, self.meeting))
        self.assertTrue(checkPerm(View, self.meeting_item))
        # Anonymous is allowed
        logout()
        self.assertTrue(checkPerm(View, self.meeting))
        self.assertTrue(checkPerm(View, self.meeting_item))
        # Editor is allowed
        login(self.portal, "editor")
        self.assertTrue(checkPerm(View, self.meeting))
        self.assertTrue(checkPerm(View, self.meeting_item))
        # Reader is allowed
        login(self.portal, "reader")
        self.assertTrue(checkPerm(View, self.meeting))
        self.assertTrue(checkPerm(View, self.meeting_item))
        # Institution Manager is allowed
        login(self.portal, "institution_manager")
        self.assertTrue(checkPerm(View, self.meeting))
        self.assertTrue(checkPerm(View, self.meeting_item))

    def testAccessContentsInformationIsNotAcquiredInPrivateState(self):
        self.assertEqual(
            self.meeting.acquiredRolesAreUsedBy(AccessContentsInformation), ""
        )  # not checked

    def testAccessContentsInformationPrivateMeeting(self):
        self.assertEqual(
            self.workflow.getInfoFor(self.meeting, "review_state"), "private"
        )
        # Owner is allowed
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting))
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting_item))
        # Member is denied
        login(self.portal, "member")
        self.assertFalse(checkPerm(AccessContentsInformation, self.meeting))
        self.assertFalse(checkPerm(AccessContentsInformation, self.meeting_item))
        # Reviewer is denied
        login(self.portal, "reviewer")
        self.assertFalse(checkPerm(AccessContentsInformation, self.meeting))
        self.assertFalse(checkPerm(AccessContentsInformation, self.meeting_item))
        # Anonymous is denied
        logout()
        self.assertFalse(checkPerm(AccessContentsInformation, self.meeting))
        self.assertFalse(checkPerm(AccessContentsInformation, self.meeting_item))
        # Editor is allowed
        login(self.portal, "editor")
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting))
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting_item))
        # Reader is allowed
        login(self.portal, "reader")
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting))
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting_item))
        # Institution Manager is allowed
        login(self.portal, "institution_manager")
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting))
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting_item))

    def testAccessContentsInformationIsNotAcquiredInPublishedState(self):
        # transition requires Review portal content
        self.workflow.doActionFor(self.meeting, "send_to_project")
        # not checked
        self.assertEqual(
            self.meeting.acquiredRolesAreUsedBy(AccessContentsInformation), ""
        )
        self.workflow.doActionFor(self.meeting, "publish")
        # not checked
        self.assertEqual(
            self.meeting.acquiredRolesAreUsedBy(AccessContentsInformation), ""
        )

    def testAccessContentsInformationInProjectMeeting(self):
        # transition requires Review portal content
        self.workflow.doActionFor(self.meeting, "send_to_project")
        # Owner is allowed
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting))
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting_item))
        # Member is allowed
        login(self.portal, "member")
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting))
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting_item))
        # Reviewer is denied but he acquires through Anonymous Role
        login(self.portal, "reviewer")
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting))
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting_item))
        # Anonymous is allowed
        logout()
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting))
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting_item))
        # Editor is allowed
        login(self.portal, "editor")
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting))
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting_item))
        # Reader is allowed
        login(self.portal, "reader")
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting))
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting_item))
        # Institution Manager is allowed
        login(self.portal, "institution_manager")
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting))
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting_item))

    def testAccessContentsInformationPublishedMeeting(self):
        # transition requires Review portal content
        self.workflow.doActionFor(self.meeting, "send_to_project")
        self.workflow.doActionFor(self.meeting, "publish")
        # Owner is allowed
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting))
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting_item))
        # Member is allowed
        login(self.portal, "member")
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting))
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting_item))
        # Reviewer is denied but he acquires through Anonymous Role
        login(self.portal, "reviewer")
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting))
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting_item))
        # Anonymous is allowed
        logout()
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting))
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting_item))
        # Editor is allowed
        login(self.portal, "editor")
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting))
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting_item))
        # Reader is allowed
        login(self.portal, "reader")
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting))
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting_item))
        # Institution Manager is allowed
        login(self.portal, "institution_manager")
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting))
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting_item))

    def testModifyPrivateMeetingIsNotAcquiredInPrivateState(self):
        self.assertEqual(
            self.meeting.acquiredRolesAreUsedBy(ModifyPortalContent), ""
        )  # not checked

    def testModifyPrivateMeeting(self):
        self.assertEqual(
            self.workflow.getInfoFor(self.meeting, "review_state"), "private"
        )
        # Owner is allowed
        self.assertTrue(checkPerm(ModifyPortalContent, self.meeting))
        self.assertTrue(checkPerm(ModifyPortalContent, self.meeting_item))
        # Member is denied
        login(self.portal, "member")
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting))
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting_item))
        # Reviewer is denied
        login(self.portal, "reviewer")
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting))
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting_item))
        # Anonymous is denied
        logout()
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting))
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting_item))
        # Editor is allowed
        login(self.portal, "editor")
        self.assertTrue(checkPerm(ModifyPortalContent, self.meeting))
        self.assertTrue(checkPerm(ModifyPortalContent, self.meeting_item))
        # Reader is denied
        login(self.portal, "reader")
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting))
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting_item))
        # Institution Manager is allowed
        login(self.portal, "institution_manager")
        self.assertTrue(checkPerm(ModifyPortalContent, self.meeting))
        self.assertTrue(checkPerm(ModifyPortalContent, self.meeting_item))

    def testModifyPortalContentIsNotAcquiredInPublishedStates(self):
        # transition requires Review portal content
        self.workflow.doActionFor(self.meeting, "send_to_project")
        self.assertEqual(self.meeting.acquiredRolesAreUsedBy(ModifyPortalContent), "")
        self.workflow.doActionFor(self.meeting, "publish")
        self.assertEqual(self.meeting.acquiredRolesAreUsedBy(ModifyPortalContent), "")

    def testModifyInProjectMeeting(self):
        # transition requires Review portal content
        self.workflow.doActionFor(self.meeting, "send_to_project")
        # Manager is allowed
        self.assertTrue(checkPerm(ModifyPortalContent, self.meeting))
        self.assertTrue(checkPerm(ModifyPortalContent, self.meeting_item))
        # Owner is allowed
        self.assertTrue(checkPerm(ModifyPortalContent, self.meeting))
        self.assertTrue(checkPerm(ModifyPortalContent, self.meeting_item))
        # Member is denied
        login(self.portal, "member")
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting))
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting_item))
        # Reviewer is denied
        login(self.portal, "reviewer")
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting))
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting_item))
        # Anonymous is denied
        logout()
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting))
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting_item))
        # Editor is allowed
        login(self.portal, "editor")
        self.assertTrue(checkPerm(ModifyPortalContent, self.meeting))
        self.assertTrue(checkPerm(ModifyPortalContent, self.meeting_item))
        # Reader is denied
        login(self.portal, "reader")
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting))
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting_item))
        # Institution Manager is allowed
        login(self.portal, "institution_manager")
        self.assertTrue(checkPerm(ModifyPortalContent, self.meeting))
        self.assertTrue(checkPerm(ModifyPortalContent, self.meeting_item))

    def testModifyPublishedMeeting(self):
        # transition requires Review portal content
        self.workflow.doActionFor(self.meeting, "send_to_project")
        self.workflow.doActionFor(self.meeting, "publish")
        # Manager is allowed
        self.assertTrue(checkPerm(ModifyPortalContent, self.meeting))
        self.assertTrue(checkPerm(ModifyPortalContent, self.meeting_item))
        # Owner is allowed
        self.assertTrue(checkPerm(ModifyPortalContent, self.meeting))
        self.assertTrue(checkPerm(ModifyPortalContent, self.meeting_item))
        # Member is denied
        login(self.portal, "member")
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting))
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting_item))
        # Reviewer is denied
        login(self.portal, "reviewer")
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting))
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting_item))
        # Anonymous is denied
        logout()
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting))
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting_item))
        # Editor is allowed
        login(self.portal, "editor")
        self.assertTrue(checkPerm(ModifyPortalContent, self.meeting))
        self.assertTrue(checkPerm(ModifyPortalContent, self.meeting_item))
        # Reader is denied
        login(self.portal, "reader")
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting))
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting_item))
        # Institution Manager is allowed
        login(self.portal, "institution_manager")
        self.assertTrue(checkPerm(ModifyPortalContent, self.meeting))
        self.assertTrue(checkPerm(ModifyPortalContent, self.meeting_item))

    def testAddContent(self):
        # Institution Manager can add content
        login(self.portal, "institution_manager")
        self.assertTrue(checkPerm(AddPortalContent, self.city1))
        self.assertTrue(checkPerm(AddPortalContent, self.meeting))
        self.assertTrue(checkPerm(AddPortalContent, self.meeting_item))
