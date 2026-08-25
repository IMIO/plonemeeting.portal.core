# -*- coding: utf-8 -*-
from plone import api
from plonemeeting.portal.core.browser.manage_users import sync_institution_keycloak_users
from plonemeeting.portal.core.tests.portal_test_case import PmPortalDemoFunctionalTestCase
from plonemeeting.portal.core.utils import get_members_group_id
from unittest.mock import patch
from zope.component import getMultiAdapter

import os


KC_ENV_KEYS = (
    "keycloak_url",
    "keycloak_admin_user",
    "keycloak_admin_password",
    "keycloak_allowed_groups",
    "keycloak_add_user_url",
)


class TestSSOUserSync(PmPortalDemoFunctionalTestCase):
    """Sync logic between Keycloak group membership and Plone members group."""

    def setUp(self):
        super().setUp()
        self.institution.authentication = "oidc"
        self.institution.sso_realm_id = "test-realm"
        self.members_group_id = get_members_group_id(self.institution)
        self._env_snapshot = {k: os.environ.get(k) for k in KC_ENV_KEYS}
        os.environ["keycloak_url"] = "https://kc.test/"
        os.environ["keycloak_admin_user"] = "admin"
        os.environ["keycloak_admin_password"] = "pw"
        os.environ["keycloak_allowed_groups"] = '["délibérations.be"]'
        os.environ["keycloak_add_user_url"] = "https://my-formulaires.imio.be/wca/"

    def tearDown(self):
        for key, value in self._env_snapshot.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        super().tearDown()

    def _kc_users(self):
        return [
            {
                "email": "alice@example.com",
                "firstName": "Alice",
                "lastName": "Smith",
                "enabled": True,
            },
            {
                "email": "bob@example.com",
                "firstName": "Bob",
                "lastName": "Jones",
                "enabled": True,
            },
        ]

    def _members(self):
        members_group = api.group.get(self.members_group_id)
        return {m.id for m in members_group.getGroupMembers()}

    @patch("plonemeeting.portal.core.browser.manage_users.fetch_institution_keycloak_users")
    def test_sync_creates_missing_users(self, fetch_mock):
        fetch_mock.return_value = self._kc_users()
        baseline = self._members()

        created, updated, removed = sync_institution_keycloak_users(self.institution)

        self.assertEqual(created, 2)
        self.assertEqual(updated, 0)
        new_members = self._members() - baseline
        self.assertEqual(new_members, {"alice@example.com", "bob@example.com"})
        alice = api.user.get(username="alice@example.com")
        self.assertEqual(alice.getProperty("fullname"), "Alice Smith")
        self.assertEqual(alice.getProperty("email"), "alice@example.com")

    @patch("plonemeeting.portal.core.browser.manage_users.fetch_institution_keycloak_users")
    def test_sync_is_idempotent(self, fetch_mock):
        fetch_mock.return_value = self._kc_users()
        sync_institution_keycloak_users(self.institution)
        members_after_first = self._members()

        created, updated, removed = sync_institution_keycloak_users(self.institution)

        self.assertEqual(created, 0)
        self.assertEqual(updated, 0)
        self.assertEqual(self._members(), members_after_first)

    @patch("plonemeeting.portal.core.browser.manage_users.fetch_institution_keycloak_users")
    def test_sync_updates_changed_fullname(self, fetch_mock):
        fetch_mock.return_value = self._kc_users()
        sync_institution_keycloak_users(self.institution)

        fetch_mock.return_value = [
            {
                "email": "alice@example.com",
                "firstName": "Alice",
                "lastName": "Smith-Married",
                "enabled": True,
            },
            self._kc_users()[1],
        ]

        created, updated, removed = sync_institution_keycloak_users(self.institution)

        self.assertEqual(created, 0)
        self.assertEqual(updated, 1)
        alice = api.user.get(username="alice@example.com")
        self.assertEqual(alice.getProperty("fullname"), "Alice Smith-Married")

    @patch("plonemeeting.portal.core.browser.manage_users.fetch_institution_keycloak_users")
    def test_sync_removes_stale_members(self, fetch_mock):
        fetch_mock.return_value = self._kc_users()
        sync_institution_keycloak_users(self.institution)
        self.assertIn("bob@example.com", self._members())

        # Bob disappears from Keycloak
        fetch_mock.return_value = [self._kc_users()[0]]
        created, updated, removed = sync_institution_keycloak_users(self.institution)

        self.assertEqual(removed, 1)
        self.assertNotIn("bob@example.com", self._members())
        # Bob's Plone account still exists (history preservation)
        self.assertIsNotNone(api.user.get(username="bob@example.com"))

    @patch("plonemeeting.portal.core.browser.manage_users.fetch_institution_keycloak_users")
    def test_sync_skips_disabled_and_empty_email_users(self, fetch_mock):
        fetch_mock.return_value = [
            {"email": "active@example.com", "firstName": "A", "lastName": "X", "enabled": True},
            {"email": "disabled@example.com", "firstName": "D", "lastName": "X", "enabled": False},
            {"email": "", "firstName": "Empty", "lastName": "Mail", "enabled": True},
        ]

        created, _, _ = sync_institution_keycloak_users(self.institution)

        self.assertEqual(created, 1)
        self.assertIn("active@example.com", self._members())
        self.assertNotIn("disabled@example.com", self._members())

    @patch("plonemeeting.portal.core.browser.manage_users.fetch_institution_keycloak_users")
    def test_sync_returns_none_when_fetch_returns_none(self, fetch_mock):
        """When prerequisites are missing fetch returns None, sync signals failure."""
        fetch_mock.return_value = None
        baseline = self._members()

        result = sync_institution_keycloak_users(self.institution)

        self.assertIsNone(result)
        self.assertEqual(self._members(), baseline)

    def test_fetch_skips_when_no_realm(self):
        """Without a realm on the institution, no HTTP is attempted."""
        from plonemeeting.portal.core.keycloak import fetch_institution_keycloak_users

        self.institution.sso_realm_id = ""
        with patch("plonemeeting.portal.core.keycloak.requests") as requests_mock:
            self.assertIsNone(fetch_institution_keycloak_users(self.institution))
            requests_mock.post.assert_not_called()
            requests_mock.get.assert_not_called()

    def test_get_keycloak_realms_returns_realm_dicts(self):
        """get_keycloak_realms extracts realm name + displayName from the admin API."""
        from plonemeeting.portal.core.keycloak import get_keycloak_realms

        with patch("plonemeeting.portal.core.keycloak.requests") as requests_mock:
            requests_mock.get.return_value.status_code = 200
            requests_mock.get.return_value.json.return_value = [
                {"realm": "master"},
                {"realm": "belle-ville", "displayName": "Belle Ville"},
            ]
            self.assertEqual(
                get_keycloak_realms("token"),
                [
                    {"realm": "master", "displayName": ""},
                    {"realm": "belle-ville", "displayName": "Belle Ville"},
                ],
            )

    def test_migrate_local_user_to_sso(self):
        """A local account is merged into its SSO identity: groups + content
        move over, the local account is deleted, and a timestamped publication
        keeps its (eIDAS) timestamp intact."""
        from collective.timestamp.interfaces import ITimeStamper
        from plone import api
        from plone.namedfile.file import NamedBlobFile
        from plonemeeting.portal.core.browser.manage_users import (
            migrate_institution_local_users,
        )

        self.login_as_admin()
        # Local account, member of the institution, with an email.
        self.portal.acl_users._doAddUser("jsmith", "pw", [], [])
        api.user.get("jsmith").setMemberProperties(mapping={"email": "j.smith@example.com"})
        api.group.add_user(groupname=self.members_group_id, username="jsmith")
        # Matching SSO account (userid == email).
        self.portal.acl_users._doAddUser("j.smith@example.com", "pw", [], [])
        # A *timestamped* publication authored by the local account.
        pub = api.content.create(
            container=self.institution.publications, type="Publication", id="pub-x", title="X"
        )
        pub.creators = ("jsmith",)
        pub.timestamp = NamedBlobFile(data=b"fake-tsr", filename="timestamp.tsr")
        pub.reindexObject()
        self.assertTrue(ITimeStamper(pub).is_timestamped())

        # The migration now syncs the Keycloak accounts first; keep the test
        # offline and focused on the migration mechanics.
        with patch(
            "plonemeeting.portal.core.browser.manage_users.sync_institution_keycloak_users",
            return_value=(0, 0, 0),
        ):
            summary = migrate_institution_local_users(self.institution)

        self.assertIn(("jsmith", "j.smith@example.com"), summary["migrated"])
        self.assertIsNone(api.user.get("jsmith"))
        members = {m.id for m in api.group.get(self.members_group_id).getGroupMembers()}
        self.assertIn("j.smith@example.com", members)
        migrated_pub = self.institution.publications["pub-x"]
        self.assertEqual(migrated_pub.creators, ("j.smith@example.com",))
        # The migration must NOT fire ObjectModifiedEvent, which would wipe the
        # timestamp (see events.publication.publication_modified).
        self.assertIsNotNone(migrated_pub.timestamp)
        self.assertTrue(ITimeStamper(migrated_pub).is_timestamped())

    def test_migrate_user_to_user_with_mismatched_email(self):
        """Manual migration pairs a local account with an SSO account whose userid
        is NOT its email (jdupont@ -> jean.dupont@) -- the case the email-based
        migration cannot match: groups + content move, the source is deleted."""
        from plonemeeting.portal.core.browser.manage_users import migrate_institution_user

        self.login_as_admin()
        # Local account whose email does not match the target SSO userid.
        self.portal.acl_users._doAddUser("jdupont", "pw", [], [])
        api.user.get("jdupont").setMemberProperties(mapping={"email": "jdupont@example.com"})
        api.group.add_user(groupname=self.members_group_id, username="jdupont")
        # SSO account with a different userid.
        self.portal.acl_users._doAddUser("jean.dupont@example.com", "pw", [], [])
        pub = api.content.create(
            container=self.institution.publications, type="Publication", id="pub-y", title="Y"
        )
        pub.creators = ("jdupont",)
        pub.reindexObject()

        count = migrate_institution_user(self.institution, "jdupont", "jean.dupont@example.com")

        self.assertEqual(count, 1)
        self.assertIsNone(api.user.get("jdupont"))
        self.assertIn("jean.dupont@example.com", self._members())
        self.assertEqual(
            self.institution.publications["pub-y"].creators, ("jean.dupont@example.com",)
        )

    def test_fetch_skips_when_no_admin_credentials(self):
        """Without admin env vars, no HTTP is attempted."""
        from plonemeeting.portal.core.keycloak import fetch_institution_keycloak_users

        os.environ.pop("keycloak_admin_user", None)
        with patch("plonemeeting.portal.core.keycloak.requests") as requests_mock:
            self.assertIsNone(fetch_institution_keycloak_users(self.institution))
            requests_mock.post.assert_not_called()

    @patch("plonemeeting.portal.core.browser.manage_users.fetch_institution_keycloak_users")
    def test_sync_marks_sso_accounts(self, fetch_mock):
        """The sync flags provisioned accounts with account_type == 'sso'."""
        fetch_mock.return_value = self._kc_users()
        sync_institution_keycloak_users(self.institution)

        alice = api.user.get(username="alice@example.com")
        self.assertEqual(alice.getProperty("account_type"), "sso")

    @patch("plonemeeting.portal.core.browser.manage_users.fetch_institution_keycloak_users")
    def test_sync_protects_local_accounts(self, fetch_mock):
        """A local member (not SSO-marked) is never purged by the SSO sync."""
        fetch_mock.return_value = self._kc_users()
        self.portal.acl_users._doAddUser("localuser", "pw", [], [])
        api.group.add_user(groupname=self.members_group_id, username="localuser")

        sync_institution_keycloak_users(self.institution)

        local = api.user.get(username="localuser")
        self.assertNotEqual(local.getProperty("account_type"), "sso")
        # Not in Keycloak, yet kept because it is not an SSO-managed account
        self.assertIn("localuser", self._members())

    @patch("plonemeeting.portal.core.browser.manage_users.fetch_institution_keycloak_users")
    def test_listing_syncs_on_each_load(self, fetch_mock):
        """The unified listing reconciles with Keycloak on every load (no cache)."""
        fetch_mock.return_value = self._kc_users()
        listing = getMultiAdapter(
            (self.institution, self.portal.REQUEST), name="manage-users-listing"
        )
        listing()
        self.assertTrue(listing.is_sso_institution)
        self.assertFalse(listing.sso_sync_failed)
        self.assertEqual(fetch_mock.call_count, 1)

        listing()
        self.assertEqual(fetch_mock.call_count, 2)

    @patch("plonemeeting.portal.core.browser.manage_users.fetch_institution_keycloak_users")
    def test_listing_renders_sso_row(self, fetch_mock):
        """A synced SSO account renders the SSO pill, the SSO edit link and no
        unregister button (guards the tal:repeat/tal:define ordering)."""
        fetch_mock.return_value = self._kc_users()
        listing = getMultiAdapter(
            (self.institution, self.portal.REQUEST), name="manage-users-listing"
        )
        html = listing()
        self.assertIn("text-bg-info", html)  # SSO pill
        self.assertIn("@@manage-edit-sso-user?username=alice@example.com", html)
        self.assertNotIn(
            "@@manage-edit-user?username=alice@example.com", html
        )  # no local edit link for an SSO account
        self.assertIn("https://my-formulaires.imio.be/wca/", html)  # "Add users" button

    @patch("plonemeeting.portal.core.browser.manage_users.fetch_institution_keycloak_users")
    def test_listing_flags_sync_failure(self, fetch_mock):
        """When Keycloak is unreachable the listing flags the failure."""
        fetch_mock.return_value = None
        listing = getMultiAdapter(
            (self.institution, self.portal.REQUEST), name="manage-users-listing"
        )
        listing()
        self.assertTrue(listing.is_sso_institution)
        self.assertTrue(listing.sso_sync_failed)
