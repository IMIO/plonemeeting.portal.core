# -*- coding: utf-8 -*-
from plone import api
from plone.app.testing import applyProfile
from plone.app.testing import login
from plone.app.testing import logout
from plonemeeting.portal.core.testing import (
    PLONEMEETING_PORTAL_CORE_INTEGRATION_TESTING,
)  # noqa
from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CMFCore.utils import _checkPermission as checkPerm
from Products.CMFCore.permissions import AccessContentsInformation
from Products.CMFCore.permissions import View
from Products.CMFCore.permissions import ModifyPortalContent

import unittest


WF = "meeting_workflow"


class TestMeetingWorkflow(unittest.TestCase):

    layer = PLONEMEETING_PORTAL_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.catalog = self.portal.portal_catalog
        self.workflow = self.portal.portal_workflow

        self.portal.acl_users._doAddUser("member", "secret", ["Member"], [])
        self.portal.acl_users._doAddUser("reviewer", "secret", ["Reviewer"], [])
        self.portal.acl_users._doAddUser("manager", "secret", ["Manager"], [])
        self.portal.acl_users._doAddUser("editor", " secret", ["Editor"], [])
        self.portal.acl_users._doAddUser("reader", "secret", ["Reader"], [])

        applyProfile(self.portal, "plonemeeting.portal.core:demo")
        login(self.portal, "manager")
        liege = getattr(self.portal, "liege")
        brains = api.content.find(context=liege, portal_type="Meeting")
        self.meeting = brains[0].getObject()

    def _check_state(self, obj, expected_review_state):
        current_state = self.workflow.getInfoFor(obj, "review_state")
        self.assertEqual(
            current_state,
            expected_review_state,
            "Object {0} should have review state {1} but has {2}".format(
                obj, expected_review_state, current_state
            ),
        )

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
        # Member is denied
        login(self.portal, "member")
        self.assertFalse(checkPerm(View, self.meeting))
        # Reviewer is denied
        login(self.portal, "reviewer")
        self.assertFalse(checkPerm(View, self.meeting))
        # Anonymous is denied
        logout()
        self.assertFalse(checkPerm(View, self.meeting))
        # Editor is allowed
        login(self.portal, "editor")
        self.assertTrue(checkPerm(View, self.meeting))
        # Reader is allowed
        login(self.portal, "reader")
        self.assertTrue(checkPerm(View, self.meeting))

    def testViewIsNotAcquiredInPublishedState(self):
        # transition requires Review portal content
        login(self.portal, "manager")
        self.workflow.doActionFor(self.meeting, "send_to_project")
        self.workflow.doActionFor(self.meeting, "publish")
        self.assertEqual(self.meeting.acquiredRolesAreUsedBy(View), "")  # not checked

    def testViewPublishedMeeting(self):
        # transition requires Review portal content
        login(self.portal, "manager")
        self.workflow.doActionFor(self.meeting, "send_to_project")
        self.workflow.doActionFor(self.meeting, "publish")
        # Owner is allowed
        self.assertTrue(checkPerm(View, self.meeting))
        # Member is allowed
        login(self.portal, "member")
        self.assertTrue(checkPerm(View, self.meeting))
        # Reviewer is denied  but he acquires through Anonymous Role
        login(self.portal, "reviewer")
        self.assertTrue(checkPerm(View, self.meeting))
        # Anonymous is allowed
        logout()
        self.assertTrue(checkPerm(View, self.meeting))
        # Editor is allowed
        login(self.portal, "editor")
        self.assertTrue(checkPerm(View, self.meeting))
        # Reader is allowed
        login(self.portal, "reader")
        self.assertTrue(checkPerm(View, self.meeting))

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
        # Member is denied
        login(self.portal, "member")
        self.assertFalse(checkPerm(AccessContentsInformation, self.meeting))
        # Reviewer is denied
        login(self.portal, "reviewer")
        self.assertFalse(checkPerm(AccessContentsInformation, self.meeting))
        # Anonymous is denied
        logout()
        self.assertFalse(checkPerm(AccessContentsInformation, self.meeting))
        # Editor is allowed
        login(self.portal, "editor")
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting))
        # Reader is allowed
        login(self.portal, "reader")
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting))

    def testAccessContentsInformationIsNotAcquiredInPublishedState(self):
        # transition requires Review portal content
        self.workflow.doActionFor(self.meeting, "send_to_project")
        self.workflow.doActionFor(self.meeting, "publish")
        # not checked
        self.assertEqual(
            self.meeting.acquiredRolesAreUsedBy(AccessContentsInformation), ""
        )

    def testAccessContentsInformationPublishedMeeting(self):
        # transition requires Review portal content
        self.workflow.doActionFor(self.meeting, "send_to_project")
        self.workflow.doActionFor(self.meeting, "publish")
        # Owner is allowed
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting))
        # Member is allowed
        login(self.portal, "member")
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting))
        # Reviewer is denied but he acquires through Anonymous Role
        login(self.portal, "reviewer")
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting))
        # Anonymous is allowed
        logout()
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting))
        # Editor is allowed
        login(self.portal, "editor")
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting))
        # Reader is allowed
        login(self.portal, "reader")
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting))

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
        # Member is denied
        login(self.portal, "member")
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting))
        # Reviewer is denied
        login(self.portal, "reviewer")
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting))
        # Anonymous is denied
        logout()
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting))
        # Editor is allowed
        login(self.portal, "editor")
        self.assertTrue(checkPerm(ModifyPortalContent, self.meeting))
        # Reader is denied
        login(self.portal, "reader")
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting))

    def testModifyPortalContentIsNotAcquiredInPublishedState(self):
        # transition requires Review portal content
        self.workflow.doActionFor(self.meeting, "send_to_project")
        self.workflow.doActionFor(self.meeting, "publish")
        self.assertEqual(self.meeting.acquiredRolesAreUsedBy(ModifyPortalContent), "")

    def testModifyPublishedMeeting(self):
        # transition requires Review portal content
        self.workflow.doActionFor(self.meeting, "send_to_project")
        self.workflow.doActionFor(self.meeting, "publish")
        # Manager is allowed
        self.assertTrue(checkPerm(ModifyPortalContent, self.meeting))
        # Owner is allowed
        self.assertTrue(checkPerm(ModifyPortalContent, self.meeting))
        # Member is denied
        login(self.portal, "member")
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting))
        # Reviewer is denied
        login(self.portal, "reviewer")
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting))
        # Anonymous is denied
        logout()
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting))
        # Editor is allowed
        login(self.portal, "editor")
        self.assertTrue(checkPerm(ModifyPortalContent, self.meeting))
        # Reader is denied
        login(self.portal, "reader")
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting))
