# -*- coding: utf-8 -*-
from plonemeeting.portal.core import _
from plonemeeting.portal.core import logger
from plonemeeting.portal.core import plausible
from Products.Five.browser import BrowserView

import requests


class BaseStatisticsView(BrowserView):
    """Embed a Plausible shared dashboard.

    The shared link (and the Plausible site itself) is (re)provisioned on
    every access through Plausible's idempotent "find or create" API. We do
    not cache the auth token: the dashboard is a cross-origin iframe, so the
    server can never tell that an embedded link went stale. Re-provisioning
    each time always yields a currently valid token and lets the dashboard
    self-heal when a link is deleted, rotated or invalidated on Plausible's
    side (e.g. after a domain change)."""

    label = _("Statistics")
    error_message = None
    embed_url = None

    @property
    def site_id(self):
        raise NotImplementedError

    @property
    def embed_script_url(self):
        return plausible.build_embed_script_url()

    def __call__(self):
        self.error_message = None
        self.embed_url = None
        if not plausible.is_plausible_configured():
            self.error_message = _("The Plausible API key is not configured. Statistics cannot be displayed.")
            return self.index()
        try:
            token = plausible.fetch_shared_link_token(self.site_id)
            self.embed_url = plausible.build_embed_url(self.site_id, token)
        except (requests.exceptions.RequestException, plausible.PlausibleError):
            logger.exception("Unable to set up the Plausible shared link for %s", self.site_id)
            self.error_message = _("Unable to retrieve statistics from Plausible. Please try again later.")
        return self.index()


class InstitutionStatisticsView(BaseStatisticsView):
    """Plausible dashboard of a single institution, for portal managers."""

    @property
    def site_id(self):
        return f"{plausible.get_plausible_site_domain()}/{self.context.getId()}"


class PlausibleStatisticsControlPanelView(BaseStatisticsView):
    """Global Plausible dashboard of the whole portal, for administrators."""

    label = _("Plausible statistics")

    @property
    def site_id(self):
        return plausible.get_plausible_site_domain()
