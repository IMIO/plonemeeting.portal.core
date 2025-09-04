# -*- coding: utf-8 -*-
from plone import api
from plone.app.testing import login
from plone.app.testing import logout
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.protect.authenticator import createToken
from plone.testing.z2 import Browser
from plonemeeting.portal.core.tests.portal_test_case import PmPortalDemoFunctionalTestCase
from plonemeeting.portal.core.utils import get_decisions_managers_group_id
from plonemeeting.portal.core.utils import get_managers_group_id
from plonemeeting.portal.core.utils import get_members_group_id
from plonemeeting.portal.core.utils import get_publications_managers_group_id
from zExceptions import Unauthorized
from zope.component import getMultiAdapter

import transaction


class TestManageUsers(PmPortalDemoFunctionalTestCase):
    """Test the custom user management per institution."""

    def setUp(self):
        super().setUp()
        self.institution = self.portal["amityville"]
        self.members_group_id = get_members_group_id(self.institution)
        self.decisions_managers_group_id = get_decisions_managers_group_id(self.institution)
        self.publications_managers_group_id = get_publications_managers_group_id(self.institution)
        self.manager_group_id = get_managers_group_id(self.institution)

        self.portal.acl_users._doAddUser("testuser", "password", [], [])

        # Create the form and view instances
        self.request = self.layer['request']
        self.request.form['_authenticator'] = createToken()
        self.create_form = getMultiAdapter((self.institution, self.request), name="manage-create-user").form_instance
        self.edit_form = getMultiAdapter((self.institution, self.request), name="manage-edit-user").form_instance
        self.invite_form = getMultiAdapter((self.institution, self.request), name="manage-invite-user").form_instance
        self.listing_view = getMultiAdapter((self.institution, self.request), name="manage-users-listing")

    def _get_user_groups_id(self, username):
        return [g.getId() for g in api.group.get_groups(username=username)]

    def test_get_manageable_groups_for_user(self):
        """get_manageable_groups_for_user should return the correct groups"""

        self.login_as_admin()
        api.group.add_user(groupname=self.members_group_id, username="testuser")

        # Should not be in any manageable groups
        self.assertEqual([], self.create_form.get_manageable_groups_for_user("testuser"))

        # Add the user to a manageable group
        api.group.add_user(groupname=self.decisions_managers_group_id, username="testuser")

        # Now the user should be in the decisions_managers group
        self.assertIn(
            self.decisions_managers_group_id,
            self.create_form.get_manageable_groups_for_user("testuser")
        )

        # Add the user to another manageable group
        api.group.add_user(groupname=self.publications_managers_group_id, username="testuser")

        # Now the user should be in both manageable groups
        manageable_groups = self.create_form.get_manageable_groups_for_user("testuser")
        self.assertIn(self.decisions_managers_group_id, manageable_groups)
        self.assertIn(self.publications_managers_group_id, manageable_groups)

    def test_update_user_groups(self):
        """update_user_groups should correctly updates the user's group memberships"""
        self.login_as_admin()
        user_groups = self._get_user_groups_id(username="testuser")
        self.assertEqual(1, len(user_groups))
        self.assertEqual("AuthenticatedUsers", user_groups[0])
        self.edit_form()

        # Add the user to the decisions_managers group
        selected_groups = [self.decisions_managers_group_id]
        self.edit_form.update_user_groups("testuser", selected_groups)

        # Check that the user is now in the decisions_managers group
        user_groups = self._get_user_groups_id(username="testuser")
        self.assertEqual(2, len(user_groups))
        self.assertIn(self.decisions_managers_group_id, user_groups)

        # Update to add the user to the publications_managers group and remove from decisions_managers
        selected_groups = [self.publications_managers_group_id]
        self.edit_form.update_user_groups("testuser", selected_groups)

        # Check that the user is now only in the publications_managers group
        user_groups = self._get_user_groups_id(username="testuser")
        self.assertEqual(2, len(user_groups))
        self.assertIn(self.publications_managers_group_id, user_groups)

        # Update to add the user to both groups
        selected_groups = [self.decisions_managers_group_id, self.publications_managers_group_id]
        self.edit_form.update_user_groups("testuser", selected_groups)

        # Check that the user is now in both groups
        user_groups = self._get_user_groups_id(username="testuser")
        self.assertEqual(3, len(user_groups))
        self.assertIn(self.decisions_managers_group_id, user_groups)
        self.assertIn(self.publications_managers_group_id, user_groups)

        # Update to remove the user from all groups
        selected_groups = []
        self.edit_form.update_user_groups("testuser", selected_groups)

        # Check that the user is not in any groups
        user_groups = self._get_user_groups_id(username="testuser")
        self.assertEqual(1, len(user_groups))
        self.assertEqual("AuthenticatedUsers", user_groups[0])

    def test_join_institution(self):
        """join_institution adds the user to the institution members group"""
        self.login_as_admin()
        self.invite_form()
        # Initially the user should not be in the members group
        self.assertNotIn(
            self.members_group_id,
            self._get_user_groups_id(username="testuser")
        )

        # Add the user to the institution
        self.invite_form.join_institution("testuser")

        # Check that the user is now in the members group
        self.assertIn(
            self.members_group_id,
            self._get_user_groups_id(username="testuser")
        )

    def test_invite_form(self):
        """handleInvite should correctly adds the user to the institution."""
        self.login_as_admin()

        # Initially the user should not be in the members group
        self.assertNotIn(
            self.members_group_id,
            self._get_user_groups_id(username="testuser")
        )

        # Set up the form data
        self.request.form['form.widgets.username'] = "testuser"
        self.request.form['form.buttons.invite'] = "Invite"

        # Process the form
        self.invite_form.update()

        # Check that the user is now in the members group
        self.assertIn(
            self.members_group_id,
            self._get_user_groups_id(username="testuser")
        )

    def test_unregister_from_institution(self):
        """unregister_from_institution should removes the user from all institution groups"""
        self.login_as_admin()
        self.edit_form()
        # Add the user to all institution groups
        api.group.add_user(groupname=self.members_group_id, username="testuser")
        api.group.add_user(groupname=self.decisions_managers_group_id, username="testuser")
        api.group.add_user(groupname=self.publications_managers_group_id, username="testuser")

        # Check that the user is in all groups
        user_groups = self._get_user_groups_id(username="testuser")
        self.assertIn(self.members_group_id, user_groups)
        self.assertIn(self.decisions_managers_group_id, user_groups)
        self.assertIn(self.publications_managers_group_id, user_groups)

        # Unregister the user from the institution
        self.edit_form.unregister_from_institution("testuser")

        # Check that the user is not in any institution groups
        user_groups = self._get_user_groups_id(username="testuser")
        self.assertNotIn(self.members_group_id, user_groups)
        self.assertNotIn(self.decisions_managers_group_id, user_groups)
        self.assertNotIn(self.publications_managers_group_id, user_groups)

    def test_get_all_institution_users(self):
        """get_all_institution_users returns all users in the institution"""
        self.login_as_admin()
        self.portal.acl_users._doAddUser("testuser1", "password", [], [])
        self.portal.acl_users._doAddUser("testuser2", "password", [], [])
        self.listing_view()
        # Initially there should be some users in the institution (from the demo setup)
        initial_users = self.institution.get_all_institution_users()
        initial_count = len(initial_users)

        # Add testuser1 to the institution
        api.group.add_user(groupname=self.members_group_id, username="testuser1")

        # Check that testuser1 is now in the list
        users = self.institution.get_all_institution_users()
        self.assertEqual(initial_count + 1, len(users))
        self.assertIn("testuser1", [user.getId() for user in users])

        # Add testuser2 to the institution
        api.group.add_user(groupname=self.members_group_id, username="testuser2")

        # Check that both users are now in the list
        users = self.institution.get_all_institution_users()
        self.assertEqual(initial_count + 2, len(users))
        user_ids = [user.getId() for user in users]
        self.assertIn("testuser1", user_ids)
        self.assertIn("testuser2", user_ids)

    def test_edit_form_updateWidgets(self):
        """updateWidgets should correctly fill the form widgets"""
        self.login_as_admin()

        # Set up a member with properties
        member = api.user.get(username="testuser")
        member.setMemberProperties(mapping={"email": "test@example.com", "fullname": "Test User"})

        # Add the user to a manageable group
        api.group.add_user(groupname=self.decisions_managers_group_id, username="testuser")

        # Set the username in the request
        self.request.form['username'] = "testuser"

        # Update the form
        self.edit_form.update()

        # Check that the widgets are correctly populated
        self.assertEqual("testuser", self.edit_form.widgets["username"].value)
        self.assertEqual("test@example.com", self.edit_form.widgets["email"].value)
        self.assertEqual("Test User", self.edit_form.widgets["fullname"].value)
        self.assertEqual([self.decisions_managers_group_id], self.edit_form.widgets["user_groups"].value)

    def test_view_form_permission_access(self):
        """Only users with in the manager group of the instution can access the manage users views and forms"""
        app = self.layer['app']
        browser = Browser(app)
        browser.handleErrors = True

        # Views to test
        views = [
            "manage-users-listing",
            "manage-create-user",
            "manage-edit-user",
            "manage-invite-user",
        ]

        # Test access for anonymous users (should be denied)
        for view in views:
            url = f"{self.institution.absolute_url()}/{view}"
            browser.open(url)
            # User should be redirected to login page
            self.assertIn(f"login?came_from=/plone/{self.institution.getId()}/{view}", browser.url)

        # Create a new user with no special permissions at first
        self.portal.acl_users._doAddUser("perm-testuser", "password", [], [])
        transaction.commit()
        user_authorization_header = "Basic perm-testuser:password"

        # Test access for regular members (should be denied)
        browser = Browser(app)
        browser.handleErrors = False
        browser.addHeader('Authorization', user_authorization_header)
        for view in views:
            url = f"{self.institution.absolute_url()}/{view}"
            with self.assertRaises(Unauthorized):
                browser.open(url)

        # Test access for institution members (should be denied)
        api.group.add_user(groupname=self.members_group_id, username="perm-testuser")
        transaction.commit()
        for view in views:
            url = f"{self.institution.absolute_url()}/{view}"
            with self.assertRaises(Unauthorized):
                browser.open(url)

        # Test access for decisions managers (should be denied)
        api.group.add_user(groupname=self.decisions_managers_group_id , username="perm-testuser")
        transaction.commit()
        for view in views:
            url = f"{self.institution.absolute_url()}/{view}"
            with self.assertRaises(Unauthorized):
                browser.open(url)

        # Test access for publications managers (should be denied)
        api.group.add_user(groupname=self.publications_managers_group_id , username="perm-testuser")
        transaction.commit()
        for view in views:
            url = f"{self.institution.absolute_url()}/{view}"
            with self.assertRaises(Unauthorized):
                browser.open(url)

        # Test access for site managers (should be allowed)
        api.group.add_user(groupname=self.manager_group_id , username="perm-testuser")
        transaction.commit()
        for view in views:
            url = f"{self.institution.absolute_url()}/{view}"
            browser.open(url)
            self.assertEqual(browser.url, url)

    def test_user_form_handleSave(self):
        """ManageCreateUserForm.handleSave should correctly create a new user with the provided properties and group memberships"""
        self.login_as_admin()

        new_username = "newuser"
        new_email = "newuser@example.com"
        new_fullname = "New User"
        new_groups = [self.decisions_managers_group_id]

        # User doesn't exist yet
        self.assertIsNone(api.user.get(username=new_username))

        # Set up the form data
        self.request.form['form.widgets.username'] = new_username
        self.request.form['form.widgets.email'] = new_email
        self.request.form['form.widgets.fullname'] = new_fullname
        self.request.form['form.widgets.user_groups'] = new_groups
        self.request.form['form.buttons.save'] = "Save"

        self.create_form()
        self.create_form.handleSave(action="save", form=self.create_form)

        # Verify the user was created with the correct properties
        user = api.user.get(username=new_username)
        self.assertIsNotNone(user)
        self.assertEqual(new_email, user.getProperty("email"))
        self.assertEqual(new_fullname, user.getProperty("fullname"))

        # Verify the user was added to the institution
        user_groups = self._get_user_groups_id(username=new_username)
        self.assertIn(self.members_group_id, user_groups)

        # Verify the user was assigned to the correct groups
        self.assertIn(self.decisions_managers_group_id, user_groups)


        updated_email = "updated@example.com"
        updated_fullname = "Updated User"
        updated_groups = [self.publications_managers_group_id]

        self.request.form['form.widgets.username'] = new_username
        self.request.form['form.widgets.email'] = updated_email
        self.request.form['form.widgets.fullname'] = updated_fullname
        self.request.form['form.widgets.user_groups'] = updated_groups
        self.request.form['form.buttons.save'] = "Save"

        self.edit_form()
        self.edit_form.handleSave(action="save", form=self.edit_form)

        # User's properties were updated
        user = api.user.get(username=new_username)
        self.assertEqual(updated_email, user.getProperty("email"))
        self.assertEqual(updated_fullname, user.getProperty("fullname"))

        # User's group memberships were updated
        user_groups = self._get_user_groups_id(username=new_username)
        self.assertIn(self.members_group_id, user_groups)  # Should still be in the institution
        self.assertNotIn(self.decisions_managers_group_id, user_groups)  # Should be removed
        self.assertIn(self.publications_managers_group_id, user_groups)  # Should be added
