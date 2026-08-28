# -*- coding: utf-8 -*-
from plone import api
from plone.protect.authenticator import createToken
from plonemeeting.portal.core import keycloak
from plonemeeting.portal.core import oidc
from plonemeeting.portal.core.browser.manage_users import sync_institution_keycloak_users
from plonemeeting.portal.core.tests.portal_test_case import PmPortalDemoFunctionalTestCase
from plonemeeting.portal.core.utils import get_decisions_managers_group_id
from plonemeeting.portal.core.utils import get_members_group_id
from Products.statusmessages.interfaces import IStatusMessage
from unittest.mock import MagicMock
from unittest.mock import patch
from zope.component import getMultiAdapter

import os
import requests


def _kc_resp(status_code=200, json_data=None, raise_json=False, text=""):
    """Build a fake ``requests`` response for the Keycloak admin-API helpers."""
    response = MagicMock()
    response.status_code = status_code
    response.text = text
    if raise_json:
        response.json.side_effect = ValueError("no json")
    else:
        response.json.return_value = json_data
    return response


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

    # -- keycloak.get_allowed_groups ---------------------------------------

    def test_get_allowed_groups_empty(self):
        os.environ["keycloak_allowed_groups"] = "   "
        self.assertEqual(keycloak.get_allowed_groups(), ())
        os.environ.pop("keycloak_allowed_groups", None)
        self.assertEqual(keycloak.get_allowed_groups(), ())

    def test_get_allowed_groups_bare_string_is_single_group(self):
        os.environ["keycloak_allowed_groups"] = "not-json"
        self.assertEqual(keycloak.get_allowed_groups(), ("not-json",))

    def test_get_allowed_groups_json_string_is_single_group(self):
        os.environ["keycloak_allowed_groups"] = '"single"'
        self.assertEqual(keycloak.get_allowed_groups(), ("single",))

    def test_get_allowed_groups_json_list_drops_empties(self):
        os.environ["keycloak_allowed_groups"] = '["a", "", "b"]'
        self.assertEqual(keycloak.get_allowed_groups(), ("a", "b"))

    # -- keycloak._keycloak_base_url ---------------------------------------

    def test_keycloak_base_url_none_when_unset(self):
        os.environ.pop("keycloak_url", None)
        self.assertIsNone(keycloak._keycloak_base_url())

    # -- keycloak.get_admin_access_token -----------------------------------

    def test_get_admin_access_token_missing_credentials(self):
        os.environ.pop("keycloak_admin_user", None)
        self.assertIsNone(keycloak.get_admin_access_token())

    def test_get_admin_access_token_success(self):
        with patch("plonemeeting.portal.core.keycloak.requests.post") as post:
            post.return_value = _kc_resp(200, {"access_token": "tok"})
            self.assertEqual(keycloak.get_admin_access_token(), "tok")

    def test_get_admin_access_token_transport_error(self):
        with patch("plonemeeting.portal.core.keycloak.requests.post") as post:
            post.side_effect = requests.RequestException("boom")
            self.assertIsNone(keycloak.get_admin_access_token())

    def test_get_admin_access_token_http_error(self):
        with patch("plonemeeting.portal.core.keycloak.requests.post") as post:
            post.return_value = _kc_resp(500, text="err")
            self.assertIsNone(keycloak.get_admin_access_token())

    def test_get_admin_access_token_not_json(self):
        with patch("plonemeeting.portal.core.keycloak.requests.post") as post:
            post.return_value = _kc_resp(200, raise_json=True)
            self.assertIsNone(keycloak.get_admin_access_token())

    def test_get_admin_access_token_missing_token(self):
        with patch("plonemeeting.portal.core.keycloak.requests.post") as post:
            post.return_value = _kc_resp(200, {})
            self.assertIsNone(keycloak.get_admin_access_token())

    # -- keycloak.get_keycloak_realms (error branches) ---------------------

    def test_get_keycloak_realms_no_base_url(self):
        os.environ.pop("keycloak_url", None)
        self.assertEqual(keycloak.get_keycloak_realms("tok"), [])

    def test_get_keycloak_realms_transport_error(self):
        with patch("plonemeeting.portal.core.keycloak.requests.get") as get:
            get.side_effect = requests.RequestException("boom")
            self.assertEqual(keycloak.get_keycloak_realms("tok"), [])

    def test_get_keycloak_realms_http_error(self):
        with patch("plonemeeting.portal.core.keycloak.requests.get") as get:
            get.return_value = _kc_resp(503)
            self.assertEqual(keycloak.get_keycloak_realms("tok"), [])

    def test_get_keycloak_realms_not_json(self):
        with patch("plonemeeting.portal.core.keycloak.requests.get") as get:
            get.return_value = _kc_resp(200, raise_json=True)
            self.assertEqual(keycloak.get_keycloak_realms("tok"), [])

    # -- keycloak.get_keycloak_group_id ------------------------------------

    def test_get_keycloak_group_id_no_base_url(self):
        os.environ.pop("keycloak_url", None)
        with self.assertRaises(keycloak.KeycloakUnavailable):
            keycloak.get_keycloak_group_id("realm", "grp", "tok")

    def test_get_keycloak_group_id_transport_error(self):
        with patch("plonemeeting.portal.core.keycloak.requests.get") as get:
            get.side_effect = requests.RequestException("boom")
            with self.assertRaises(keycloak.KeycloakUnavailable):
                keycloak.get_keycloak_group_id("realm", "grp", "tok")

    def test_get_keycloak_group_id_http_error(self):
        with patch("plonemeeting.portal.core.keycloak.requests.get") as get:
            get.return_value = _kc_resp(404)
            with self.assertRaises(keycloak.KeycloakUnavailable):
                keycloak.get_keycloak_group_id("realm", "grp", "tok")

    def test_get_keycloak_group_id_not_json(self):
        with patch("plonemeeting.portal.core.keycloak.requests.get") as get:
            get.return_value = _kc_resp(200, raise_json=True)
            with self.assertRaises(keycloak.KeycloakUnavailable):
                keycloak.get_keycloak_group_id("realm", "grp", "tok")

    def test_get_keycloak_group_id_found_and_absent(self):
        with patch("plonemeeting.portal.core.keycloak.requests.get") as get:
            get.return_value = _kc_resp(
                200, [{"name": "grp", "id": "gid"}, {"name": "other", "id": "x"}]
            )
            self.assertEqual(keycloak.get_keycloak_group_id("realm", "grp", "tok"), "gid")
            get.return_value = _kc_resp(200, [{"name": "other", "id": "x"}])
            self.assertIsNone(keycloak.get_keycloak_group_id("realm", "grp", "tok"))

    # -- keycloak.get_keycloak_group_members -------------------------------

    def test_get_keycloak_group_members_no_base_url(self):
        os.environ.pop("keycloak_url", None)
        with self.assertRaises(keycloak.KeycloakUnavailable):
            keycloak.get_keycloak_group_members("realm", "gid", "tok")

    def test_get_keycloak_group_members_transport_error(self):
        with patch("plonemeeting.portal.core.keycloak.requests.get") as get:
            get.side_effect = requests.RequestException("boom")
            with self.assertRaises(keycloak.KeycloakUnavailable):
                keycloak.get_keycloak_group_members("realm", "gid", "tok")

    def test_get_keycloak_group_members_http_error(self):
        with patch("plonemeeting.portal.core.keycloak.requests.get") as get:
            get.return_value = _kc_resp(500)
            with self.assertRaises(keycloak.KeycloakUnavailable):
                keycloak.get_keycloak_group_members("realm", "gid", "tok")

    def test_get_keycloak_group_members_not_json(self):
        with patch("plonemeeting.portal.core.keycloak.requests.get") as get:
            get.return_value = _kc_resp(200, raise_json=True)
            with self.assertRaises(keycloak.KeycloakUnavailable):
                keycloak.get_keycloak_group_members("realm", "gid", "tok")

    def test_get_keycloak_group_members_success(self):
        with patch("plonemeeting.portal.core.keycloak.requests.get") as get:
            get.return_value = _kc_resp(200, [{"email": "a@x"}])
            self.assertEqual(
                keycloak.get_keycloak_group_members("realm", "gid", "tok"),
                [{"email": "a@x"}],
            )

    # -- keycloak.fetch_institution_keycloak_users -------------------------

    def test_fetch_skips_when_no_allowed_groups(self):
        os.environ.pop("keycloak_allowed_groups", None)
        with patch("plonemeeting.portal.core.keycloak.get_admin_access_token") as token:
            self.assertIsNone(keycloak.fetch_institution_keycloak_users(self.institution))
            token.assert_not_called()

    def test_fetch_returns_none_when_no_token(self):
        with patch("plonemeeting.portal.core.keycloak.get_admin_access_token", return_value=None):
            self.assertIsNone(keycloak.fetch_institution_keycloak_users(self.institution))

    def test_fetch_happy_path_unions_members_by_email(self):
        os.environ["keycloak_allowed_groups"] = '["g1", "g2"]'
        with patch(
            "plonemeeting.portal.core.keycloak.get_admin_access_token", return_value="tok"
        ), patch(
            "plonemeeting.portal.core.keycloak.get_keycloak_group_id", side_effect=["id1", "id2"]
        ), patch(
            "plonemeeting.portal.core.keycloak.get_keycloak_group_members",
            side_effect=[
                [{"email": "a@x"}, {"email": ""}],
                [{"email": "a@x"}, {"email": "b@y"}],
            ],
        ):
            users = keycloak.fetch_institution_keycloak_users(self.institution)
        self.assertEqual(sorted(u["email"] for u in users), ["a@x", "b@y"])

    def test_fetch_skips_group_that_does_not_exist(self):
        os.environ["keycloak_allowed_groups"] = '["missing", "present"]'
        with patch(
            "plonemeeting.portal.core.keycloak.get_admin_access_token", return_value="tok"
        ), patch(
            "plonemeeting.portal.core.keycloak.get_keycloak_group_id", side_effect=[None, "id2"]
        ), patch(
            "plonemeeting.portal.core.keycloak.get_keycloak_group_members",
            return_value=[{"email": "c@z"}],
        ):
            users = keycloak.fetch_institution_keycloak_users(self.institution)
        self.assertEqual([u["email"] for u in users], ["c@z"])

    def test_fetch_aborts_when_group_unavailable(self):
        os.environ["keycloak_allowed_groups"] = '["g1"]'
        with patch(
            "plonemeeting.portal.core.keycloak.get_admin_access_token", return_value="tok"
        ), patch(
            "plonemeeting.portal.core.keycloak.get_keycloak_group_id",
            side_effect=keycloak.KeycloakUnavailable("boom"),
        ):
            self.assertIsNone(keycloak.fetch_institution_keycloak_users(self.institution))

    def test_fetch_returns_none_when_no_group_resolved(self):
        os.environ["keycloak_allowed_groups"] = '["missing"]'
        with patch(
            "plonemeeting.portal.core.keycloak.get_admin_access_token", return_value="tok"
        ), patch(
            "plonemeeting.portal.core.keycloak.get_keycloak_group_id", return_value=None
        ):
            self.assertIsNone(keycloak.fetch_institution_keycloak_users(self.institution))

    # -- oidc --------------------------------------------------------------

    def _oidc_plugin_or_skip(self):
        plugin = oidc.get_oidc_plugin()
        if plugin is None:
            self.skipTest("pas.plugins.oidc plugin not present in this environment")
        return plugin

    def test_setup_oidc_plugin_configures_client(self):
        plugin = self._oidc_plugin_or_skip()
        with patch.dict(
            os.environ,
            {
                "keycloak_issuer": "https://kc.test/realms/master",
                "keycloak_client_id": "portal",
                "keycloak_client_secret": "secret",
            },
        ):
            result = oidc.setup_oidc_plugin()
        self.assertIsNotNone(result)
        self.assertEqual(result.getId(), plugin.getId())
        self.assertEqual(plugin.issuer, "https://kc.test/realms/master")
        self.assertEqual(plugin.client_id, "portal")
        self.assertTrue(plugin.create_user)
        self.assertFalse(plugin.create_groups)
        self.assertEqual(plugin.redirect_uris, ("/acl_users/oidc/callback",))

    def test_setup_oidc_plugin_none_when_plugin_missing(self):
        with patch("plonemeeting.portal.core.oidc.get_oidc_plugin", return_value=None):
            self.assertIsNone(oidc.setup_oidc_plugin())

    def test_disable_oidc_challenge_noop_when_issuer_set(self):
        plugin = self._oidc_plugin_or_skip()
        plugin.issuer = "https://kc.test/realms/master"
        self.assertIsNone(oidc.disable_oidc_challenge_if_unconfigured())

    def test_get_login_url_none_without_issuer(self):
        self._oidc_plugin_or_skip().issuer = ""
        self.assertIsNone(oidc.get_login_url())

    def test_get_login_url_with_came_from(self):
        self._oidc_plugin_or_skip().issuer = "https://kc.test/realms/master"
        url = oidc.get_login_url(came_from="/amityville/publications")
        self.assertIn("/acl_users/oidc/login", url)
        self.assertIn("came_from=", url)

    # -- manage_users: SSO edit form ---------------------------------------

    def _admin_request(self):
        self.login_as_admin()
        request = self.layer["request"]
        request.form["_authenticator"] = createToken()
        return request

    def _error_messages(self, request):
        return [m for m in IStatusMessage(request).show() if m.type == "error"]

    def _provision_alice(self):
        with patch(
            "plonemeeting.portal.core.browser.manage_users.fetch_institution_keycloak_users",
            return_value=self._kc_users(),
        ):
            sync_institution_keycloak_users(self.institution)

    def test_sso_edit_form_updateWidgets_prefills_readonly(self):
        self._provision_alice()
        request = self._admin_request()
        request.form["username"] = "alice@example.com"
        form = getMultiAdapter(
            (self.institution, request), name="manage-edit-sso-user"
        ).form_instance
        form.update()
        self.assertEqual(form.widgets["email"].value, "alice@example.com")
        self.assertEqual(form.widgets["email"].readonly, "readonly")
        self.assertEqual(form.widgets["fullname"].readonly, "readonly")
        self.assertEqual(form.widgets["username"].readonly, "readonly")

    def test_sso_edit_form_handleSave_updates_groups(self):
        self._provision_alice()
        request = self._admin_request()
        decisions_group = get_decisions_managers_group_id(self.institution)
        request.form["form.widgets.username"] = "alice@example.com"
        # The readonly identity widgets post their value back.
        request.form["form.widgets.email"] = "alice@example.com"
        request.form["form.widgets.user_groups"] = [decisions_group]
        request.form["form.buttons.save"] = "Save"
        form = getMultiAdapter(
            (self.institution, request), name="manage-edit-sso-user"
        ).form_instance
        form()
        form.handleSave(action="save", form=form)
        groups = [g.getId() for g in api.group.get_groups(username="alice@example.com")]
        self.assertIn(decisions_group, groups)

    def test_sso_edit_form_handleSave_rejects_non_member(self):
        request = self._admin_request()
        request.form["form.widgets.username"] = "not-a-member@example.com"
        request.form["form.buttons.save"] = "Save"
        form = getMultiAdapter(
            (self.institution, request), name="manage-edit-sso-user"
        ).form_instance
        form()
        form.handleSave(action="save", form=form)
        self.assertTrue(self._error_messages(request))

    # -- manage_users: local -> SSO migration ------------------------------

    def test_migrate_local_users_returns_none_on_sync_failure(self):
        from plonemeeting.portal.core.browser.manage_users import migrate_institution_local_users

        with patch(
            "plonemeeting.portal.core.browser.manage_users.sync_institution_keycloak_users",
            return_value=None,
        ):
            self.assertIsNone(migrate_institution_local_users(self.institution))

    def test_migrate_local_users_skips_sso_and_unmatched(self):
        from plonemeeting.portal.core.browser.manage_users import migrate_institution_local_users

        self.login_as_admin()
        # An SSO-marked member: skipped (already migrated).
        self.portal.acl_users._doAddUser("sso.member@example.com", "pw", [], [])
        api.user.get("sso.member@example.com").setMemberProperties(
            mapping={"email": "sso.member@example.com", "account_type": "sso"}
        )
        api.group.add_user(groupname=self.members_group_id, username="sso.member@example.com")
        # A local member with no matching SSO account: skipped (nothing to migrate onto).
        self.portal.acl_users._doAddUser("lonelylocal", "pw", [], [])
        api.user.get("lonelylocal").setMemberProperties(
            mapping={"email": "lonelylocal@example.com"}
        )
        api.group.add_user(groupname=self.members_group_id, username="lonelylocal")
        with patch(
            "plonemeeting.portal.core.browser.manage_users.sync_institution_keycloak_users",
            return_value=(0, 0, 0),
        ):
            summary = migrate_institution_local_users(self.institution)
        self.assertIn("lonelylocal", summary["skipped"])
        self.assertNotIn("sso.member@example.com", summary["skipped"])

    def test_migrate_reassigns_local_roles(self):
        """migrate_institution_user moves Owner local roles from source to target."""
        from plonemeeting.portal.core.browser.manage_users import migrate_institution_user

        self.login_as_admin()
        self.portal.acl_users._doAddUser("roleuser", "pw", [], [])
        api.user.get("roleuser").setMemberProperties(mapping={"email": "roleuser@example.com"})
        api.group.add_user(groupname=self.members_group_id, username="roleuser")
        self.portal.acl_users._doAddUser("roleuser@example.com", "pw", [], [])
        pub = api.content.create(
            container=self.institution.publications, type="Publication", id="pub-roles", title="R"
        )
        pub.creators = ("roleuser",)
        pub.manage_addLocalRoles("roleuser", ["Owner"])
        pub.reindexObject()

        count = migrate_institution_user(self.institution, "roleuser", "roleuser@example.com")

        self.assertEqual(count, 1)
        role_holders = [userid for userid, roles in pub.get_local_roles()]
        self.assertIn("roleuser@example.com", role_holders)
        self.assertNotIn("roleuser", role_holders)

    def _add_migratable_local_user(self, local_id, email):
        self.portal.acl_users._doAddUser(local_id, "pw", [], [])
        api.user.get(local_id).setMemberProperties(mapping={"email": email})
        api.group.add_user(groupname=self.members_group_id, username=local_id)
        self.portal.acl_users._doAddUser(email, "pw", [], [])

    def test_migrate_view_local_users_rows(self):
        self._provision_alice()  # alice/bob are SSO-marked and must be excluded
        self.login_as_admin()
        self._add_migratable_local_user("localx", "localx@example.com")
        view = getMultiAdapter(
            (self.institution, self.layer["request"]), name="migrate-institution-users"
        )
        rows = view.local_users()
        ids = [row["id"] for row in rows]
        self.assertIn("localx", ids)
        self.assertNotIn("alice@example.com", ids)
        localx_row = next(row for row in rows if row["id"] == "localx")
        self.assertTrue(localx_row["ready"])

    def test_migrate_view_post_migrates(self):
        self.login_as_admin()
        self._add_migratable_local_user("poste", "poste@example.com")
        request = self._admin_request()
        request.method = "POST"
        with patch(
            "plonemeeting.portal.core.browser.manage_users.sync_institution_keycloak_users",
            return_value=(0, 0, 0),
        ):
            view = getMultiAdapter((self.institution, request), name="migrate-institution-users")
            result = view()
        self.assertEqual(result, "")
        self.assertIsNone(api.user.get("poste"))

    def test_migrate_view_post_reports_sync_failure(self):
        request = self._admin_request()
        request.method = "POST"
        with patch(
            "plonemeeting.portal.core.browser.manage_users.sync_institution_keycloak_users",
            return_value=None,
        ):
            view = getMultiAdapter((self.institution, request), name="migrate-institution-users")
            result = view()
        self.assertEqual(result, "")
        self.assertTrue(self._error_messages(request))

    def test_migrate_view_get_renders(self):
        self.login_as_admin()
        request = self.layer["request"]
        request.method = "GET"
        view = getMultiAdapter((self.institution, request), name="migrate-institution-users")
        self.assertIsInstance(view(), str)

    def test_migrate_user_to_user_form_handleMigrate(self):
        from plonemeeting.portal.core.browser.manage_users import MigrateUserToUserForm

        self.login_as_admin()
        self._add_migratable_local_user("m2m", "m2m.target@example.com")
        request = self._admin_request()
        form = getMultiAdapter(
            (self.institution, request), name="migrate-institution-user"
        ).form_instance
        form.update()
        rows = [{"source": "m2m", "target": "m2m.target@example.com"}]
        with patch.object(MigrateUserToUserForm, "extractData", return_value=({"migrations": rows}, [])):
            form.handleMigrate(action="migrate", form=form)
        self.assertIsNone(api.user.get("m2m"))

    def test_migrate_user_to_user_form_handleMigrate_with_errors(self):
        from plonemeeting.portal.core.browser.manage_users import MigrateUserToUserForm

        request = self._admin_request()
        form = getMultiAdapter(
            (self.institution, request), name="migrate-institution-user"
        ).form_instance
        form.update()
        with patch.object(MigrateUserToUserForm, "extractData", return_value=({}, [object()])):
            form.handleMigrate(action="migrate", form=form)
        self.assertTrue(self._error_messages(request))
