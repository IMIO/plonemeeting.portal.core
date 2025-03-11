# my/product/tests/test_manage_users.py

import unittest
from plone.testing.z2 import Browser
from plone.app.testing import login, logout, TEST_USER_NAME, TEST_USER_ID, setRoles
from Products.CMFCore.utils import getToolByName

from plonemeeting.portal.core.tests.portal_test_case import PmPortalTestCase


class TestManageUsers(PmPortalTestCase):
    """Integration tests for the custom user manager (focusing on groups)."""

    def setUp(self):
        self.portal = self.layer['portal']
        self.app = self.layer['app']
        self.browser = Browser(self.app)
        self.browser.handleErrors = False

        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        login(self.portal, TEST_USER_NAME)

        # We'll reference these tools often
        self.acl_users = getToolByName(self.portal, 'acl_users')
        self.group_tool = getToolByName(self.portal, 'portal_groups')
        self.membership = getToolByName(self.portal, 'portal_membership')

    def tearDown(self):
        logout()

    def test_1_listing_view_no_users(self):
        """Check listing view 'no users found' message when only default test user remains."""
        # Remove all users except the default test user
        for uid in list(self.acl_users.getUserIds()):
            if uid != TEST_USER_ID:
                self.acl_users.userFolderDelUsers([uid])

        self.browser.open(self.portal.absolute_url() + '/manage-users-listing')
        self.assertIn(
            'No users found.',
            self.browser.contents,
            "Expected 'No users found.' message not present in listing."
        )

    def test_2_create_user_via_form(self):
        """Create a new user from the form, assign one group, verify they appear in listing."""
        self.browser.open(self.portal.absolute_url() + '/manage-users-form')

        # Fill out form
        self.browser.getControl(label='User ID').value = 'alice'
        self.browser.getControl(label='Email').value = 'alice@example.com'
        self.browser.getControl(label='Full name').value = 'Alice Wonderland'

        # Assign one group (assuming the label is the group ID or something close)
        # Depending on how your widget is rendered, you might see the label 'managers'
        self.browser.getControl(label='managers').selected = True

        self.browser.getControl(name='form.buttons.save').click()

        # Check listing
        self.assertIn('manage-users-listing', self.browser.url, "Did not return to listing after save.")
        self.assertIn('alice', self.browser.contents, "New user 'alice' not found in listing.")

        # Verify group membership
        group_obj = self.group_tool.getGroupById('managers')
        self.assertIn('alice', group_obj.getGroupMemberIds(), "'alice' not actually in 'managers' group.")

    def test_3_edit_user_update_groups(self):
        """Edit existing user to change group membership."""
        # Pre-create a user 'bob'
        reg = getToolByName(self.portal, 'portal_registration')
        reg.addMember('bob', 'secret', properties={'email': 'bob@oldmail.com', 'fullname': 'Bob Oldname'})

        # Add him to 'editors' group
        self.group_tool.addPrincipalToGroup('bob', 'editors')

        # Now open the form with user_id=bob
        self.browser.open(self.portal.absolute_url() + '/manage-users-form?user_id=bob')

        # Suppose we want to remove 'editors' and add 'managers'
        self.browser.getControl(label='editors').selected = False
        self.browser.getControl(label='managers').selected = True

        self.browser.getControl(label='Email').value = 'bob@newmail.com'
        self.browser.getControl(label='Full name').value = 'Bob Newname'
        self.browser.getControl(name='form.buttons.save').click()

        # Confirm changes in listing
        self.assertIn('manage-users-listing', self.browser.url, "No redirect to listing after update.")
        self.assertIn('bob', self.browser.contents, "Updated user 'bob' not found in listing.")

        # Confirm new membership
        managers_group = self.group_tool.getGroupById('managers')
        editors_group = self.group_tool.getGroupById('editors')
        self.assertIn('bob', managers_group.getGroupMemberIds(), "User 'bob' not added to 'managers'.")
        self.assertNotIn('bob', editors_group.getGroupMemberIds(), "User 'bob' was not removed from 'editors'.")

    def test_4_delete_user(self):
        """Delete a user via the form, ensure they're removed from all groups and membership."""
        reg = getToolByName(self.portal, 'portal_registration')
        reg.addMember('charlie', 'secret', properties={'email': 'charlie@example.com'})

        # Put 'charlie' in 'managers' and 'editors'
        self.group_tool.addPrincipalToGroup('charlie', 'managers')
        self.group_tool.addPrincipalToGroup('charlie', 'editors')

        self.browser.open(self.portal.absolute_url() + '/manage-users-form?user_id=charlie&delete=1')
        self.assertIn('manage-users-listing', self.browser.url, "Did not redirect to listing after delete.")

        # Confirm 'charlie' is gone from membership
        self.assertIsNone(self.membership.getMemberById('charlie'), "User 'charlie' still exists after delete.")

        # Confirm 'charlie' is gone from groups
        for group_id in ['managers', 'editors']:
            group_obj = self.group_tool.getGroupById(group_id)
            self.assertNotIn('charlie', group_obj.getGroupMemberIds(), f"'charlie' still in group {group_id}.")

    def test_5_assign_multiple_groups_on_create(self):
        """Create user with multiple groups at once, verify membership."""
        self.browser.open(self.portal.absolute_url() + '/manage-users-form')
        self.browser.getControl(label='User ID').value = 'diana'
        self.browser.getControl(label='Email').value = 'diana@example.com'
        self.browser.getControl(label='Full name').value = 'Diana MultiGroups'

        # Assign 'managers' and 'editors'
        self.browser.getControl(label='managers').selected = True
        self.browser.getControl(label='editors').selected = True

        self.browser.getControl(name='form.buttons.save').click()
        self.assertIn('manage-users-listing', self.browser.url, "Did not return to listing after create.")

        # Verify group memberships
        for group_id in ['managers', 'editors']:
            group_obj = self.group_tool.getGroupById(group_id)
            self.assertIn('diana', group_obj.getGroupMemberIds(), f"'diana' missing from {group_id} group.")
        reviewers_group = self.group_tool.getGroupById('reviewers')
        self.assertNotIn('diana', reviewers_group.getGroupMemberIds(), "Unexpected membership in 'reviewers'.")
