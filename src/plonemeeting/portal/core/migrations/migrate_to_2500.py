# -*- coding: utf-8 -*-
from plone import api
from plonemeeting.portal.core.config import LOCAL_ACCOUNT_TYPE
from plonemeeting.portal.core.keycloak import get_admin_access_token
from plonemeeting.portal.core.keycloak import get_keycloak_realms
from plonemeeting.portal.core.migrations import PlonemeetingMigrator
from plonemeeting.portal.core.oidc import disable_oidc_challenge_if_unconfigured
from plonemeeting.portal.core.oidc import setup_oidc_plugin
from plonemeeting.portal.core.utils import get_members_group_id

import difflib
import logging


logger = logging.getLogger("plonemeeting.portal.core")


class MigrateTo2500(PlonemeetingMigrator):
    @staticmethod
    def _match_realm(institution, realms):
        """Fuzzy-match an institution to a Keycloak realm, scanning both sides:
        institution id vs realm name (slugs), then title vs displayName (labels).
        Returns the realm name, or None if nothing is close enough."""
        by_slug = {realm["realm"]: realm["realm"] for realm in realms}
        by_label = {realm["displayName"]: realm["realm"] for realm in realms if realm["displayName"]}
        for value, table in ((institution.getId(), by_slug), (institution.Title(), by_label)):
            close = difflib.get_close_matches(value, list(table), n=1)
            if close:
                return table[close[0]]
        return None

    def _backfill_sso_realm_ids(self):
        """Fuzzy-fill each institution's ``sso_realm_id`` from the Keycloak realms."""
        token = get_admin_access_token()
        realms = get_keycloak_realms(token) if token else []
        if not realms:
            logger.warning("No Keycloak realms available; skipping sso_realm_id backfill")
            return
        for brain in self.catalog(portal_type="Institution"):
            institution = brain.getObject()
            realm = self._match_realm(institution, realms)
            if realm:
                institution.sso_realm_id = realm
                logger.info("Set sso_realm_id=%r on %s", realm, institution.getId())
            else:
                logger.warning("No matching Keycloak realm for %s", institution.getId())

    def _backfill_account_types(self):
        """Flag institution members that predate ``account_type`` as local.

        Only members with no value yet are touched: the step is re-runnable,
        and an account already promoted to 'sso' by the Keycloak sync must not
        be demoted back to local here -- the listing would show it as Local,
        and it would only recover on the next successful sync.
        """
        for brain in self.catalog(portal_type="Institution"):
            group = api.group.get(get_members_group_id(brain.getObject()))
            if group is None:
                continue
            for member in group.getGroupMembers():
                if member.getProperty("account_type", ""):
                    continue
                member.setMemberProperties(mapping={"account_type": LOCAL_ACCOUNT_TYPE})

    def _setup_oidc_plugin(self):
        """Install pas.plugins.oidc and configure its site-wide plugin.

        The metadata.xml dependency on pas.plugins.oidc:default only applies
        on a fresh (re)install of our profile -- upgraded sites must install
        the add-on here, or acl_users never gets the plugin. When the
        keycloak_* environment is incomplete the freshly installed plugin is
        deactivated, as its active challenge would loop on anonymous 401s.
        """
        if not self.qi.is_product_installed("pas.plugins.oidc"):
            self.qi.install_product("pas.plugins.oidc")
        if setup_oidc_plugin() is None:
            disable_oidc_challenge_if_unconfigured()

    def run(self):
        logger.info("Migrating to plonemeeting.portal.core 2500")
        profile = "profile-plonemeeting.portal.core:default"
        self.ps.runImportStepFromProfile(profile, "typeinfo")
        self.ps.runImportStepFromProfile(profile, "memberdata-properties")
        # actions -> the admin-only "Migrate users to SSO" object button
        self.ps.runImportStepFromProfile(profile, "actions")
        self._backfill_sso_realm_ids()
        self._backfill_account_types()
        self._setup_oidc_plugin()
        logger.info("Migration to plonemeeting.portal.core 2500 done.")


def migrate(context):
    """Re-import the authentication fieldset (typeinfo) and the ``account_type``
    memberdata property (memberdata), fuzzy-fill each institution's
    ``sso_realm_id`` from the Keycloak realms, then flag existing institution
    members as local accounts for the unified users management view
    (DELIBE-297)."""
    migrator = MigrateTo2500(context)
    migrator.run()
    migrator.finish()
