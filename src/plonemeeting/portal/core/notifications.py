# -*- coding: utf-8 -*-
"""Transactional notifications that ``imio.emailkit`` sends.

The kit owns the templates and their translations. This module only collects
the context and selects the recipient.
"""
from imio.emailkit import Email
from plone import api
from plonemeeting.portal.core import logger
from plonemeeting.portal.core.oidc import get_account_url
from plonemeeting.portal.core.oidc import sso_login_url


SSO_MIGRATED_TEMPLATE = "imio.emailkit:user_migrated_to_sso"
SITE_NAME = "Délibérations.be"


def notify_user_migrated_to_sso(institution, old_id, new_id):
    """Tell ``new_id`` that the portal moved ``old_id`` onto their SSO account.

    Each successful migration sends this mail: the bulk ``@@migrate-institution-users``
    run, the ``@migrate-users-to-sso`` REST endpoint and the manual
    ``@@migrate-user-to-user`` form.

    It never raises. A mail failure must not undo a migration that succeeded.
    The bulk run wraps each account in a savepoint, and an error rolls back
    that account. Returns ``True`` when the kit queues the mail, else ``False``.

    Delivery follows the transaction. If the request aborts, no mail reaches
    the MTA.
    """
    try:
        member = api.user.get(userid=new_id)
        Email(SSO_MIGRATED_TEMPLATE).to(member or new_id).with_context(
            site_name=SITE_NAME,
            institution=institution.Title(),
            email=new_id,
            username=old_id,
            login_url=sso_login_url(institution),
            # Use "" and not None, so that the template removes the
            # "change it there" link and does not show "None".
            account_url=get_account_url() or "",
        ).send()
    except Exception:
        logger.exception(
            "Could not notify %s of the migration of %s in %s",
            new_id,
            old_id,
            institution.getId(),
        )
        return False
    logger.info("Queued SSO migration notification for %s", new_id)
    return True
