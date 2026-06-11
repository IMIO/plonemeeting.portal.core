# -*- coding: utf-8 -*-
"""Helpers for the Plausible Analytics API (web statistics dashboards).

The portal embeds Plausible dashboards through *shared links*
(https://plausible.io/docs/shared-links): one per institution on the
``@@statistics`` view and a global one in the "Plausible statistics"
control panel. The Plausible base URL and Sites API key live in the
registry; shared link auth tokens are cached (on the institution or in
the registry) so the API is only hit on first access.
"""
from plone import api
from plonemeeting.portal.core import logger
from urllib import parse

import requests


PLAUSIBLE_API_TIMEOUT = 10


class PlausibleError(Exception):
    """The Plausible API could not deliver a usable shared link."""


def get_plausible_base_url():
    base_url = api.portal.get_registry_record("plonemeeting.portal.core.plausible_base_url", default=None)
    return (base_url or "").rstrip("/")


def get_plausible_api_key():
    return api.portal.get_registry_record("plonemeeting.portal.core.plausible_api_key", default=None) or ""


def get_plausible_site_domain():
    domain = api.portal.get_registry_record("plonemeeting.portal.core.plausible_site_domain", default=None)
    return domain or "deliberations.be"


def is_plausible_configured():
    return bool(get_plausible_base_url() and get_plausible_api_key())


def _api_headers():
    return {
        "Authorization": f"Bearer {get_plausible_api_key()}",
        "Content-Type": "application/json",
    }


def create_site(site_id):
    """Create ``site_id`` in Plausible (POST /api/v1/sites).

    A non-2xx answer is only logged: most of the time the site already
    exists, which Plausible reports as an error. If the site really could
    not be created, the subsequent shared link call fails loudly anyway.
    """
    url = f"{get_plausible_base_url()}/api/v1/sites"
    response = requests.post(url, json={"domain": site_id}, headers=_api_headers(), timeout=PLAUSIBLE_API_TIMEOUT)
    if response.status_code not in (200, 201):
        logger.info(
            "Plausible site %s not created (HTTP %s): %s", site_id, response.status_code, response.text
        )


def get_shared_link_token(site_id, name):
    """Find-or-create a shared link (PUT /api/v1/sites/shared-links,
    idempotent) and return its auth token."""
    url = f"{get_plausible_base_url()}/api/v1/sites/shared-links"
    response = requests.put(
        url, json={"site_id": site_id, "name": name}, headers=_api_headers(), timeout=PLAUSIBLE_API_TIMEOUT
    )
    if response.status_code != 200:
        raise PlausibleError(
            f"Unable to get a Plausible shared link for {site_id} (HTTP {response.status_code}): {response.text}"
        )
    shared_link_url = response.json().get("url") or ""
    token = parse.parse_qs(parse.urlparse(shared_link_url).query).get("auth")
    if not token:
        raise PlausibleError(f"No auth token in Plausible shared link for {site_id}: {shared_link_url}")
    return token[0]


def fetch_shared_link_token(site_id):
    """Provision the Plausible site if needed and return a shared link token."""
    create_site(site_id)
    return get_shared_link_token(site_id, f"Statistiques {site_id}")


def build_embed_url(site_id, token):
    return "{}/share/{}?auth={}&embed=true&theme=light&background=transparent".format(
        get_plausible_base_url(), parse.quote(site_id, safe=""), token
    )


def build_embed_script_url():
    return f"{get_plausible_base_url()}/js/embed.host.js"
