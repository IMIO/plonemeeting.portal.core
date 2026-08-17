# -*- coding: utf-8 -*-
from plonemeeting.portal.core import logger

import json
import os
import requests


ADMIN_TOKEN_TIMEOUT = 10
ADMIN_API_TIMEOUT = 30
ADMIN_API_MAX_USERS = 1000


def get_allowed_groups():
    """Keycloak groups whose members may use the portal, as a tuple.

    Read from ``keycloak_allowed_groups``, a JSON list (e.g.
    ``["délibérations.be"]``).  A bare string is accepted as a single group so
    a malformed value degrades to something usable rather than to nothing.

    The same value gates login -- it is copied to the OIDC plugin's
    ``allowed_groups`` property, which ``user_can_login()`` checks against the
    user's ``groups`` claim -- and scopes the admin-API sync below.
    """
    raw = os.environ.get("keycloak_allowed_groups", "").strip()
    if not raw:
        return ()
    try:
        groups = json.loads(raw)
    except ValueError:
        return (raw,)
    if isinstance(groups, str):
        return (groups,)
    return tuple(group for group in groups if group)


def _keycloak_base_url():
    url = os.environ.get("keycloak_url", "")
    if not url:
        return None
    return url.rstrip("/")


def get_admin_access_token():
    """Acquire a master-realm admin token via the admin-cli client (password grant).

    Returns the access token string, or None when credentials/url are missing
    or Keycloak does not return a 200 with a JSON access_token.
    """
    base_url = _keycloak_base_url()
    username = os.environ.get("keycloak_admin_user")
    password = os.environ.get("keycloak_admin_password")
    if not base_url or not username or not password:
        logger.warning("Keycloak admin credentials not configured, skipping token fetch")
        return None

    url = "{0}/realms/master/protocol/openid-connect/token".format(base_url)
    payload = {
        "client_id": "admin-cli",
        "username": username,
        "password": password,
        "grant_type": "password",
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    try:
        resp = requests.post(url, data=payload, headers=headers, timeout=ADMIN_TOKEN_TIMEOUT)
    except requests.RequestException as exc:
        logger.error("Keycloak admin token request failed: {0}".format(exc))
        return None
    if resp.status_code != 200:
        logger.error("Keycloak admin token HTTP {0}: {1}".format(resp.status_code, resp.text))
        return None
    try:
        token = resp.json().get("access_token")
    except ValueError:
        logger.error("Keycloak admin token response is not JSON")
        return None
    if not token:
        logger.error("Keycloak admin token response missing access_token")
        return None
    return token


def get_keycloak_realms(token):
    """Return the Keycloak realms as ``{"realm", "displayName"}`` dicts, or []."""
    base_url = _keycloak_base_url()
    if not base_url:
        return []
    url = "{0}/admin/realms".format(base_url)
    headers = {"Authorization": "Bearer {0}".format(token)}
    try:
        resp = requests.get(url, headers=headers, timeout=ADMIN_API_TIMEOUT)
    except requests.RequestException as exc:
        logger.error("Keycloak realms request failed: {0}".format(exc))
        return []
    if resp.status_code != 200:
        logger.error("Keycloak realms HTTP {0}".format(resp.status_code))
        return []
    try:
        return [
            {"realm": realm["realm"], "displayName": realm.get("displayName") or ""}
            for realm in resp.json()
            if realm.get("realm")
        ]
    except ValueError:
        logger.error("Keycloak realms response is not JSON")
        return []


def get_keycloak_group_id(realm, group_name, token):
    """Resolve the id of the Keycloak group named ``group_name`` in ``realm``.

    Returns the group id of the first exact-name match, or None.
    """
    base_url = _keycloak_base_url()
    if not base_url:
        return None
    url = "{0}/admin/realms/{1}/groups".format(base_url, realm)
    headers = {"Authorization": "Bearer {0}".format(token)}
    try:
        resp = requests.get(
            url, headers=headers, params={"search": group_name}, timeout=ADMIN_API_TIMEOUT
        )
    except requests.RequestException as exc:
        logger.error("Keycloak group lookup failed for realm {0}: {1}".format(realm, exc))
        return None
    if resp.status_code != 200:
        logger.error(
            "Keycloak group lookup HTTP {0} for realm {1}".format(resp.status_code, realm)
        )
        return None
    try:
        groups = resp.json()
    except ValueError:
        logger.error("Keycloak group lookup response is not JSON for realm {0}".format(realm))
        return None
    for group in groups:
        if group.get("name") == group_name:
            return group.get("id")
    logger.warning(
        "Keycloak group {0!r} not found in realm {1!r}".format(group_name, realm)
    )
    return None


def get_keycloak_group_members(realm, group_id, token):
    """Return the list of user dicts that belong to ``group_id`` in ``realm``."""
    base_url = _keycloak_base_url()
    if not base_url:
        return []
    url = "{0}/admin/realms/{1}/groups/{2}/members".format(base_url, realm, group_id)
    headers = {"Authorization": "Bearer {0}".format(token)}
    try:
        resp = requests.get(
            url, headers=headers, params={"max": ADMIN_API_MAX_USERS}, timeout=ADMIN_API_TIMEOUT
        )
    except requests.RequestException as exc:
        logger.error(
            "Keycloak group members request failed for realm {0}: {1}".format(realm, exc)
        )
        return []
    if resp.status_code != 200:
        logger.error(
            "Keycloak group members HTTP {0} for realm {1}".format(resp.status_code, realm)
        )
        return []
    try:
        return resp.json()
    except ValueError:
        logger.error("Keycloak group members response is not JSON for realm {0}".format(realm))
        return []


def fetch_institution_keycloak_users(institution):
    """Return the Keycloak users of ``institution``'s realm that belong to one
    of the allowed groups, or None when prerequisites are missing.

    A None return is the signal to callers to skip the sync — they should
    keep rendering the existing Plone-side data without raising.  An empty
    list, by contrast, means "the groups exist and nobody is in them", which
    the sync is allowed to act on.
    """
    realm = getattr(institution, "sso_realm_id", None)
    if not realm:
        logger.info(
            "Institution {0} has no sso_realm_id, skipping Keycloak sync".format(
                institution.getId()
            )
        )
        return None

    allowed_groups = get_allowed_groups()
    if not allowed_groups:
        logger.warning(
            "keycloak_allowed_groups is not set, skipping Keycloak sync for {0}".format(
                institution.getId()
            )
        )
        return None

    token = get_admin_access_token()
    if not token:
        return None

    users = {}
    resolved = 0
    for group_name in allowed_groups:
        group_id = get_keycloak_group_id(realm, group_name, token)
        if not group_id:
            continue
        resolved += 1
        for user in get_keycloak_group_members(realm, group_id, token):
            # Union across groups: a user in two allowed groups is one user.
            email = (user.get("email") or "").strip()
            if email:
                users[email] = user
    if not resolved:
        # None of the configured groups exist in this realm -- a
        # misconfiguration, not an empty group. Do not let the sync read that
        # as "every member left" and unregister them all.
        return None
    return list(users.values())
