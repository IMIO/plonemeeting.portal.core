# -*- coding: utf-8 -*-

from imio.helpers.workflow import get_transitions
from plone import api
from plone.app.testing import login
from plone.app.testing import logout
from plonemeeting.portal.core.tests.portal_test_case import PmPortalDemoFunctionalTestCase
from Products.CMFCore.permissions import AccessContentsInformation
from Products.CMFCore.permissions import AddPortalContent
from Products.CMFCore.permissions import DeleteObjects
from Products.CMFCore.permissions import ModifyPortalContent
from Products.CMFCore.permissions import View
from Products.CMFCore.utils import _checkPermission as checkPerm
from Products.CMFCore.WorkflowCore import WorkflowException


WF = "meeting_workflow"


class TestMeetingWorkflow(PmPortalDemoFunctionalTestCase):
    def setUp(self):
        super().setUp()
        self.login_as_admin()
        api.user.create(
            username="member",
            email="noreply@pm.portal",
            password="supersecret",
            roles=["Member"])
        api.user.create(
            username="reviewer",
            email="noreply@pm.portal",
            password="supersecret",
            roles=["Reviewer"])
        api.user.create(
            username="editor",
            email="noreply@pm.portal",
            password="supersecret",
            roles=["Editor"])
        api.user.create(
            username="reader",
            email="noreply@pm.portal",
            password="supersecret",
            roles=["Reader"])
        self.decisions = self.institution.decisions
        self.publications = self.institution.publications
        self.meeting = api.content.create(
            container=self.decisions,
            title="My meeting",
            type="Meeting"
        )
        self.item = api.content.create(
            container=self.meeting, title="My item", type="Item"
        )

    def tearDown(self):
        self.login_as_admin()
        api.content.delete(obj=self.meeting)
        super().tearDown()

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
        self._check_index(self.item, "linkedMeetingReviewState", "private")
        self.workflow.doActionFor(self.meeting, "send_to_project")
        self._check_index(self.item, "linkedMeetingReviewState", "in_project")
        self.workflow.doActionFor(self.meeting, "publish")
        self._check_index(self.item, "linkedMeetingReviewState", "decision")

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
        self.assertTrue(checkPerm(View, self.item))
        # Member is denied
        login(self.portal, "member")
        self.assertFalse(checkPerm(View, self.meeting))
        self.assertFalse(checkPerm(View, self.item))
        # Reviewer is denied
        login(self.portal, "reviewer")
        self.assertFalse(checkPerm(View, self.meeting))
        self.assertFalse(checkPerm(View, self.item))
        # Anonymous is denied
        logout()
        self.assertFalse(checkPerm(View, self.meeting))
        self.assertFalse(checkPerm(View, self.item))
        # Editor is allowed
        login(self.portal, "editor")
        self.assertTrue(checkPerm(View, self.meeting))
        self.assertTrue(checkPerm(View, self.item))
        # Reader is allowed
        login(self.portal, "reader")
        self.assertTrue(checkPerm(View, self.meeting))
        self.assertTrue(checkPerm(View, self.item))
        # Institution Manager is allowed
        self.login_as_decisions_manager()
        self.assertTrue(checkPerm(View, self.meeting))
        self.assertTrue(checkPerm(View, self.item))

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
        self.assertTrue(checkPerm(View, self.item))
        # Member is allowed
        login(self.portal, "member")
        self.assertTrue(checkPerm(View, self.meeting))
        self.assertTrue(checkPerm(View, self.item))
        # Reviewer is denied  but he acquires through Anonymous Role
        login(self.portal, "reviewer")
        self.assertTrue(checkPerm(View, self.meeting))
        self.assertTrue(checkPerm(View, self.item))
        # Anonymous is allowed
        logout()
        self.assertTrue(checkPerm(View, self.meeting))
        self.assertTrue(checkPerm(View, self.item))
        # Editor is allowed
        login(self.portal, "editor")
        self.assertTrue(checkPerm(View, self.meeting))
        self.assertTrue(checkPerm(View, self.item))
        # Reader is allowed
        login(self.portal, "reader")
        self.assertTrue(checkPerm(View, self.meeting))
        self.assertTrue(checkPerm(View, self.item))
        # Institution Manager is allowed
        self.login_as_decisions_manager()
        self.assertTrue(checkPerm(View, self.meeting))
        self.assertTrue(checkPerm(View, self.item))

    def testViewPublishedMeeting(self):
        # transition requires Review portal content
        login(self.portal, "manager")
        self.workflow.doActionFor(self.meeting, "send_to_project")
        self.workflow.doActionFor(self.meeting, "publish")
        # Owner is allowed
        self.assertTrue(checkPerm(View, self.meeting))
        self.assertTrue(checkPerm(View, self.item))
        # Member is allowed
        login(self.portal, "member")
        self.assertTrue(checkPerm(View, self.meeting))
        self.assertTrue(checkPerm(View, self.item))
        # Reviewer is denied  but he acquires through Anonymous Role
        login(self.portal, "reviewer")
        self.assertTrue(checkPerm(View, self.meeting))
        self.assertTrue(checkPerm(View, self.item))
        # Anonymous is allowed
        logout()
        self.assertTrue(checkPerm(View, self.meeting))
        self.assertTrue(checkPerm(View, self.item))
        # Editor is allowed
        login(self.portal, "editor")
        self.assertTrue(checkPerm(View, self.meeting))
        self.assertTrue(checkPerm(View, self.item))
        # Reader is allowed
        login(self.portal, "reader")
        self.assertTrue(checkPerm(View, self.meeting))
        self.assertTrue(checkPerm(View, self.item))
        # Institution Manager is allowed
        self.login_as_decisions_manager()
        self.assertTrue(checkPerm(View, self.meeting))
        self.assertTrue(checkPerm(View, self.item))

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
        self.assertTrue(checkPerm(AccessContentsInformation, self.item))
        # Member is denied
        login(self.portal, "member")
        self.assertFalse(checkPerm(AccessContentsInformation, self.meeting))
        self.assertFalse(checkPerm(AccessContentsInformation, self.item))
        # Reviewer is denied
        login(self.portal, "reviewer")
        self.assertFalse(checkPerm(AccessContentsInformation, self.meeting))
        self.assertFalse(checkPerm(AccessContentsInformation, self.item))
        # Anonymous is denied
        logout()
        self.assertFalse(checkPerm(AccessContentsInformation, self.meeting))
        self.assertFalse(checkPerm(AccessContentsInformation, self.item))
        # Editor is allowed
        login(self.portal, "editor")
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting))
        self.assertTrue(checkPerm(AccessContentsInformation, self.item))
        # Reader is allowed
        login(self.portal, "reader")
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting))
        self.assertTrue(checkPerm(AccessContentsInformation, self.item))
        # Institution Manager is allowed
        self.login_as_decisions_manager()
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting))
        self.assertTrue(checkPerm(AccessContentsInformation, self.item))

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
        self.assertTrue(checkPerm(AccessContentsInformation, self.item))
        # Member is allowed
        login(self.portal, "member")
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting))
        self.assertTrue(checkPerm(AccessContentsInformation, self.item))
        # Reviewer is denied but he acquires through Anonymous Role
        login(self.portal, "reviewer")
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting))
        self.assertTrue(checkPerm(AccessContentsInformation, self.item))
        # Anonymous is allowed
        logout()
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting))
        self.assertTrue(checkPerm(AccessContentsInformation, self.item))
        # Editor is allowed
        login(self.portal, "editor")
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting))
        self.assertTrue(checkPerm(AccessContentsInformation, self.item))
        # Reader is allowed
        login(self.portal, "reader")
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting))
        self.assertTrue(checkPerm(AccessContentsInformation, self.item))
        # Institution Manager is allowed
        self.login_as_decisions_manager()
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting))
        self.assertTrue(checkPerm(AccessContentsInformation, self.item))

    def testAccessContentsInformationPublishedMeeting(self):
        # transition requires Review portal content
        self.workflow.doActionFor(self.meeting, "send_to_project")
        self.workflow.doActionFor(self.meeting, "publish")
        # Owner is allowed
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting))
        self.assertTrue(checkPerm(AccessContentsInformation, self.item))
        # Member is allowed
        login(self.portal, "member")
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting))
        self.assertTrue(checkPerm(AccessContentsInformation, self.item))
        # Reviewer is denied but he acquires through Anonymous Role
        login(self.portal, "reviewer")
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting))
        self.assertTrue(checkPerm(AccessContentsInformation, self.item))
        # Anonymous is allowed
        logout()
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting))
        self.assertTrue(checkPerm(AccessContentsInformation, self.item))
        # Editor is allowed
        login(self.portal, "editor")
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting))
        self.assertTrue(checkPerm(AccessContentsInformation, self.item))
        # Reader is allowed
        login(self.portal, "reader")
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting))
        self.assertTrue(checkPerm(AccessContentsInformation, self.item))
        # Institution Manager is allowed
        self.login_as_decisions_manager()
        self.assertTrue(checkPerm(AccessContentsInformation, self.meeting))
        self.assertTrue(checkPerm(AccessContentsInformation, self.item))

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
        self.assertTrue(checkPerm(ModifyPortalContent, self.item))
        # Member is denied
        login(self.portal, "member")
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting))
        self.assertFalse(checkPerm(ModifyPortalContent, self.item))
        # Reviewer is denied
        login(self.portal, "reviewer")
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting))
        self.assertFalse(checkPerm(ModifyPortalContent, self.item))
        # Anonymous is denied
        logout()
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting))
        self.assertFalse(checkPerm(ModifyPortalContent, self.item))
        # Editor is allowed
        login(self.portal, "editor")
        self.assertTrue(checkPerm(ModifyPortalContent, self.meeting))
        self.assertTrue(checkPerm(ModifyPortalContent, self.item))
        # Reader is denied
        login(self.portal, "reader")
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting))
        self.assertFalse(checkPerm(ModifyPortalContent, self.item))
        # Institution Manager is allowed
        self.login_as_decisions_manager()
        self.assertTrue(checkPerm(ModifyPortalContent, self.meeting))
        self.assertTrue(checkPerm(ModifyPortalContent, self.item))

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
        self.assertTrue(checkPerm(ModifyPortalContent, self.item))
        # Owner is allowed
        self.assertTrue(checkPerm(ModifyPortalContent, self.meeting))
        self.assertTrue(checkPerm(ModifyPortalContent, self.item))
        # Member is denied
        login(self.portal, "member")
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting))
        self.assertFalse(checkPerm(ModifyPortalContent, self.item))
        # Reviewer is denied
        login(self.portal, "reviewer")
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting))
        self.assertFalse(checkPerm(ModifyPortalContent, self.item))
        # Anonymous is denied
        logout()
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting))
        self.assertFalse(checkPerm(ModifyPortalContent, self.item))
        # Editor is allowed
        login(self.portal, "editor")
        self.assertTrue(checkPerm(ModifyPortalContent, self.meeting))
        self.assertTrue(checkPerm(ModifyPortalContent, self.item))
        # Reader is denied
        login(self.portal, "reader")
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting))
        self.assertFalse(checkPerm(ModifyPortalContent, self.item))
        # Institution Manager is allowed
        self.login_as_decisions_manager()
        self.assertTrue(checkPerm(ModifyPortalContent, self.meeting))
        self.assertTrue(checkPerm(ModifyPortalContent, self.item))

    def testModifyPublishedMeeting(self):
        # transition requires Review portal content
        self.workflow.doActionFor(self.meeting, "send_to_project")
        self.workflow.doActionFor(self.meeting, "publish")
        # Manager is allowed
        self.assertTrue(checkPerm(ModifyPortalContent, self.meeting))
        self.assertTrue(checkPerm(ModifyPortalContent, self.item))
        # Owner is allowed
        self.assertTrue(checkPerm(ModifyPortalContent, self.meeting))
        self.assertTrue(checkPerm(ModifyPortalContent, self.item))
        # Member is denied
        login(self.portal, "member")
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting))
        self.assertFalse(checkPerm(ModifyPortalContent, self.item))
        # Reviewer is denied
        login(self.portal, "reviewer")
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting))
        self.assertFalse(checkPerm(ModifyPortalContent, self.item))
        # Anonymous is denied
        logout()
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting))
        self.assertFalse(checkPerm(ModifyPortalContent, self.item))
        # Editor is allowed
        login(self.portal, "editor")
        self.assertTrue(checkPerm(ModifyPortalContent, self.meeting))
        self.assertTrue(checkPerm(ModifyPortalContent, self.item))
        # Reader is denied
        login(self.portal, "reader")
        self.assertFalse(checkPerm(ModifyPortalContent, self.meeting))
        self.assertFalse(checkPerm(ModifyPortalContent, self.item))
        # Institution Manager is allowed
        self.login_as_decisions_manager()
        self.assertTrue(checkPerm(ModifyPortalContent, self.meeting))
        self.assertTrue(checkPerm(ModifyPortalContent, self.item))

    def testAddContent(self):
        self.login_as_admin()
        self.assertTrue(checkPerm(AddPortalContent, self.institution))
        self.assertTrue(checkPerm(AddPortalContent, self.decisions))
        self.assertTrue(checkPerm(AddPortalContent, self.meeting))
        self.assertTrue(checkPerm(AddPortalContent, self.item))
        self.assertTrue(checkPerm(AddPortalContent, self.publications))

        self.login_as_decisions_manager()
        self.assertFalse(checkPerm(AddPortalContent, self.institution))
        self.assertTrue(checkPerm(AddPortalContent, self.decisions))
        self.assertTrue(checkPerm(AddPortalContent, self.meeting))
        self.assertTrue(checkPerm(AddPortalContent, self.item))
        self.assertFalse(checkPerm(AddPortalContent, self.publications))

        self.login_as_publications_manager()
        self.assertFalse(checkPerm(AddPortalContent, self.institution))
        self.assertFalse(checkPerm(AddPortalContent, self.decisions))
        self.assertFalse(checkPerm(AddPortalContent, self.meeting))
        self.assertFalse(checkPerm(AddPortalContent, self.item))
        self.assertTrue(checkPerm(AddPortalContent, self.publications))

    def testRemoveContent(self):
        self.login_as_admin()
        self.assertTrue(checkPerm(DeleteObjects, self.institution))
        self.assertTrue(checkPerm(DeleteObjects, self.decisions))
        self.assertTrue(checkPerm(DeleteObjects, self.meeting))
        self.assertTrue(checkPerm(DeleteObjects, self.item))
        self.assertTrue(checkPerm(DeleteObjects, self.publications))

        self.login_as_decisions_manager()
        self.assertFalse(checkPerm(DeleteObjects, self.institution))
        self.assertFalse(checkPerm(DeleteObjects, self.decisions))
        self.assertFalse(checkPerm(DeleteObjects, self.meeting))
        self.assertFalse(checkPerm(DeleteObjects, self.item))
        self.assertFalse(checkPerm(DeleteObjects, self.publications))

        self.login_as_publications_manager()
        self.assertFalse(checkPerm(DeleteObjects, self.institution))
        self.assertFalse(checkPerm(DeleteObjects, self.decisions))
        self.assertFalse(checkPerm(DeleteObjects, self.meeting))
        self.assertFalse(checkPerm(DeleteObjects, self.item))
        self.assertFalse(checkPerm(DeleteObjects, self.publications))

    def test_any_decisions_manager_may_change_review_state(self):
        # private
        self.login_as_decisions_manager()
        self.assertEqual(get_transitions(self.meeting), ["send_to_project"])
        self.login_as_decisions_manager2()
        self.assertEqual(get_transitions(self.meeting), ["send_to_project"])
        # in_project
        self.workflow.doActionFor(self.meeting, "send_to_project")
        self.login_as_decisions_manager()
        self.assertEqual(sorted(get_transitions(self.meeting)),
                         ["back_to_private", "publish"])
        self.login_as_decisions_manager2()
        self.assertEqual(sorted(get_transitions(self.meeting)),
                         ["back_to_private", "publish"])
        # decision
        self.workflow.doActionFor(self.meeting, "publish")
        self.login_as_decisions_manager()
        self.assertEqual(get_transitions(self.meeting), ["back_to_project"])
        self.login_as_decisions_manager2()
        self.assertEqual(get_transitions(self.meeting), ["back_to_project"])
