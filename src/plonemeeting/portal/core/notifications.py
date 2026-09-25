# -*- coding: utf-8 -*-
"""Transactional notifications, sent through ``imio.emailkit``.

The kit owns the templates and their translations. This module only collects
the context and selects the recipient.
"""
from imio.emailkit import Email
from plone import api
from plonemeeting.portal.core import logger
from plonemeeting.portal.core.oidc import get_account_url
from plonemeeting.portal.core.oidc import get_login_url


SSO_MIGRATED_TEMPLATE = "imio.emailkit:user_migrated_to_sso"
SITE_NAME = "Délibérations.be"


def sso_login_url(institution):
    """Where a migrated user should go to log in again.

    The OIDC login URL takes them straight to Wallonie Connect and back to
    their own institution. It is ``None`` when the plugin has no issuer
    configured, and the portal's login-choice page is then the honest
    fallback: that view is registered on the site root only, so it cannot be
    built from the institution.
    """
    login_url = get_login_url(came_from=institution.absolute_url())
    return login_url or f"{api.portal.get().absolute_url()}/@@login-choice"


def notify_user_migrated_to_sso(institution, old_id, new_id):
    """Tell ``new_id`` that ``old_id`` was migrated onto their SSO account.

    Sent for every successful migration, wherever it came from: the bulk
    ``@@migrate-institution-users`` run, its ``@migrate-users-to-sso`` REST
    equivalent, or the manual ``@@migrate-user-to-user`` form.

    Never raises. A mail that cannot be built or queued must not undo a
    migration that already succeeded -- the bulk run wraps each account in a
    transaction savepoint and would roll that whole account back. Returns
    whether the mail was queued.

    Delivery is the kit's default, which is transaction-bound: nothing reaches
    the MTA if the request that migrated the account ends up aborting.
    """
    try:
        member = api.user.get(userid=new_id)
        Email(SSO_MIGRATED_TEMPLATE).to(member or new_id).with_context(
            site_name=SITE_NAME,
            institution=institution.Title(),
            email=new_id,
            username=old_id,
            login_url=sso_login_url(institution),
            # Empty rather than None when Keycloak is unconfigured: the
            # template drops the "change it there" link instead of printing
            # "None" at the reader.
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
