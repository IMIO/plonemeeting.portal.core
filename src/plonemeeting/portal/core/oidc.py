# -*- coding: utf-8 -*-
"""Configuration of the site-wide OIDC (Keycloak) login plugin.

``pas.plugins.oidc`` installs a single plugin in ``acl_users`` (id ``oidc``);
this module points it at the Keycloak realm and client described by the
environment.  Institutions do not get their own plugin: they all authenticate
against the same realm, and the ``sso_realm_id`` field only scopes the
admin-API user sync in ``keycloak.py``.
"""
from pas.plugins.oidc import PLUGIN_ID as OIDC_PLUGIN_ID
from plone import api
from plonemeeting.portal.core import logger
from plonemeeting.portal.core.keycloak import get_allowed_groups
from urllib.parse import quote

import os


def get_oidc_plugin():
    """The site-wide OIDC plugin, or None when the add-on is not installed."""
    acl_users = api.portal.get_tool("acl_users")
    return getattr(acl_users, OIDC_PLUGIN_ID, None)


def setup_oidc_plugin():
    """Point the site-wide OIDC plugin at the configured Keycloak client.

    Returns the plugin, or None when it is missing or the environment is
    incomplete.
    """
    plugin = get_oidc_plugin()
    if plugin is None:
        logger.warning("No {0!r} plugin in acl_users, skipping OIDC setup".format(OIDC_PLUGIN_ID))
        return None

    issuer = os.environ.get("keycloak_issuer", "")
    client_id = os.environ.get("keycloak_client_id", "")
    client_secret = os.environ.get("keycloak_client_secret", "")
    if not issuer or not client_id or not client_secret:
        logger.warning(
            "keycloak_issuer/keycloak_client_id/keycloak_client_secret not set, "
            "skipping OIDC setup"
        )
        return None

    plugin.issuer = issuer
    plugin.client_id = client_id
    plugin.client_secret = client_secret
    # Stored relative: pas.plugins.oidc prefixes the portal url at runtime, so
    # the redirect uri follows a domain change without a migration.
    plugin.redirect_uris = ("/acl_users/{0}/callback".format(OIDC_PLUGIN_ID),)
    plugin.create_user = True
    plugin.create_groups = False
    # Login gate: user_can_login() checks these against the user's ``groups``
    # claim, so only members of the portal's Keycloak group get in.
    plugin.allowed_groups = get_allowed_groups()
    logger.info("Configured OIDC plugin {0!r} for issuer {1}".format(OIDC_PLUGIN_ID, issuer))
    return plugin


def disable_oidc_challenge_if_unconfigured():
    """Stop an unconfigured OIDC plugin from answering anonymous 401s.

    ``pas.plugins.oidc``'s post_install puts its plugin at the top of
    ``IChallengePlugin``.  With no issuer set -- a fresh install, or any
    environment without the keycloak_* variables -- challenging redirects to
    an empty issuer and loops instead of showing Plone's login form.  Once the
    plugin is configured the challenge is left alone.
    """
    plugin = get_oidc_plugin()
    if plugin is None or plugin.getProperty("issuer"):
        return None
    plugin.manage_activateInterfaces([])
    logger.info(
        "Deactivated the {0!r} plugin: no issuer configured".format(OIDC_PLUGIN_ID)
    )
    return plugin


def get_login_url(came_from=None):
    """URL that starts the OIDC login flow, or None when the plugin is
    missing or has no issuer configured (callers then fall back to the
    classic Plone login form)."""
    plugin = get_oidc_plugin()
    if plugin is None or not plugin.getProperty("issuer"):
        return None
    url = "{0}/acl_users/{1}/login".format(api.portal.get().absolute_url(), OIDC_PLUGIN_ID)
    if came_from:
        url = "{0}?came_from={1}".format(url, quote(came_from))
    return url
