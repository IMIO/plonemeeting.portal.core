# -*- coding: utf-8 -*-
from plone import api
from plone.registry.field import TextLine
from plone.registry.interfaces import IRegistry
from plone.registry.record import Record
from plonemeeting.portal.core.browser.manage_users import LOCAL_ACCOUNT_TYPE
from plonemeeting.portal.core.keycloak import get_admin_access_token
from plonemeeting.portal.core.keycloak import get_keycloak_realms
from plonemeeting.portal.core.migrations import PlonemeetingMigrator
from plonemeeting.portal.core.utils import get_members_group_id
from zope.component import getUtility

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
        """Flag every existing institution member as a local account.

        SSO accounts get promoted to 'sso' automatically the next time the
        Keycloak sync runs on the users listing.
        """
        for brain in self.catalog(portal_type="Institution"):
            group = api.group.get(get_members_group_id(brain.getObject()))
            if group is None:
                continue
            for member in group.getGroupMembers():
                member.setMemberProperties(mapping={"account_type": LOCAL_ACCOUNT_TYPE})

    def _register_sso_management_url(self):
        """Add the sso_management_url registry record (KISS: just this record,
        so we don't re-apply the whole registry.xml)."""
        registry = getUtility(IRegistry)
        key = "plonemeeting.portal.core.sso_management_url"
        if key not in registry.records:
            registry.records[key] = Record(
                TextLine(title="SSO user management URL"), "https://my.imio.be"
            )

    def run(self):
        logger.info("Migrating to plonemeeting.portal.core 2500")
        profile = "profile-plonemeeting.portal.core:default"
        # typeinfo -> authentication fieldset on Institution
        # memberdata -> account_type property (memberdata_properties.xml)
        self.ps.runImportStepFromProfile(profile, "typeinfo")
        self.ps.runImportStepFromProfile(profile, "memberdata")
        # actions -> the admin-only "Migrate users to SSO" object button
        self.ps.runImportStepFromProfile(profile, "actions")
        self._register_sso_management_url()
        self._backfill_sso_realm_ids()
        self._backfill_account_types()
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
