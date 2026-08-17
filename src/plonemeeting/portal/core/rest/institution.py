# -*- coding: utf-8 -*-
from plone.protect.interfaces import IDisableCSRFProtection
from plone.restapi.services import Service
from plonemeeting.portal.core.browser.manage_users import migrate_institution_local_users
from zope.interface import alsoProvides


class MigrateInstitutionUsersService(Service):
    """POST @migrate-users-to-sso on an Institution.

    Same operation as the ``@@migrate-institution-users`` button: sync the
    institution's Keycloak accounts, then migrate its local accounts (group
    memberships, owned content, deletion) to their SSO identity.  Exposed as
    a REST endpoint so it can be triggered remotely (e.g. from Rundeck).
    """

    def reply(self):
        # Deliberate write on POST, authenticated via the REST API.
        alsoProvides(self.request, IDisableCSRFProtection)
        summary = migrate_institution_local_users(self.context)
        if summary is None:
            self.request.response.setStatus(503)
            return {
                "error": {
                    "type": "ServiceUnavailable",
                    "message": "The SSO server could not be reached; nothing was migrated.",
                }
            }
        return {
            "migrated": [{"old": old, "new": new} for old, new in summary["migrated"]],
            "skipped": summary["skipped"],
            "content": summary["content"],
        }
