# -*- coding: utf-8 -*-
"""Transactional notifications, rendered and sent through ``imio.emailkit``.

The portal sent no mail of its own before this module; installing the kit also
restyles the mails Plone itself sends (password reset, registration,
username reminder), which needs no code.

Everything here goes through the kit's generic ``imio.emailkit:notification``
template: a title, an intro paragraph and one call to action. Its *subject* is
an i18n message the kit translates per recipient, but its body values are plain
context strings inserted verbatim, so they are translated here -- into the
recipient's own language -- before being handed over.
"""
from imio.emailkit import Email
from plone import api
from plonemeeting.portal.core import _
from plonemeeting.portal.core import logger
from plonemeeting.portal.core.oidc import get_login_url


NOTIFICATION_TEMPLATE = "imio.emailkit:notification"


def recipient_language(member):
    """The language a mail to ``member`` should be rendered in.

    ``portal_memberdata``'s ``language`` property is empty for everyone who
    never expressed a preference, and it is always empty on an account the
    OIDC plugin provisioned at first login, so the site's default language is
    the answer for very nearly every recipient.
    """
    language = ""
    if member is not None:
        language = (member.getProperty("language", "") or "").strip()
    return language or api.portal.get_default_language()


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
        language = recipient_language(member)
        intro = _(
            "email_intro_sso_migrated",
            default="Your access to ${institution} on Délibérations.be is now managed "
            "by Wallonie Connect. From now on, log in with Wallonie Connect using the "
            "address ${email}. Your former username ${username} and its password no "
            "longer work.",
            mapping={
                "institution": institution.Title(),
                "email": new_id,
                "username": old_id,
            },
        )
        Email(NOTIFICATION_TEMPLATE).to(member or new_id).subject(
            _(
                "email_subject_sso_migrated",
                default="Your Délibérations.be account now uses Wallonie Connect",
            )
        ).with_context(
            title=api.portal.translate(
                _(
                    "email_title_sso_migrated",
                    default="Your account now uses Wallonie Connect",
                ),
                lang=language,
            ),
            intro=api.portal.translate(intro, lang=language),
            cta_label=api.portal.translate(
                _("email_cta_sso_migrated", default="Log in with Wallonie Connect"),
                lang=language,
            ),
            cta_url=sso_login_url(institution),
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
