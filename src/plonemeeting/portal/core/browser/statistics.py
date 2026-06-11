# -*- coding: utf-8 -*-
from plone import api
from plone.protect.interfaces import IDisableCSRFProtection
from plonemeeting.portal.core import _
from plonemeeting.portal.core import logger
from plonemeeting.portal.core import plausible
from Products.Five.browser import BrowserView
from zope.interface import alsoProvides

import requests


PLAUSIBLE_TOKEN_REGISTRY_KEY = "plonemeeting.portal.core.plausible_shared_link_token"


class BaseStatisticsView(BrowserView):
    """Embed a Plausible shared dashboard, provisioning the shared link
    (and the Plausible site itself) on first access. The auth token is
    cached by subclasses so later accesses don't hit the Plausible API."""

    label = _("Statistics")
    error_message = None
    embed_url = None

    @property
    def site_id(self):
        raise NotImplementedError

    def get_stored_token(self):
        raise NotImplementedError

    def store_token(self, token):
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
        token = self.get_stored_token()
        if not token:
            try:
                token = plausible.fetch_shared_link_token(self.site_id)
                # Caching the token writes to the database on a GET request:
                # tell plone.protect this write is intentional, otherwise the
                # first visit triggers the CSRF confirmation page.
                alsoProvides(self.request, IDisableCSRFProtection)
                self.store_token(token)
            except (requests.exceptions.RequestException, plausible.PlausibleError):
                logger.exception("Unable to set up the Plausible shared link for %s", self.site_id)
        if token:
            self.embed_url = plausible.build_embed_url(self.site_id, token)
        else:
            self.error_message = _("Unable to retrieve statistics from Plausible. Please try again later.")
        return self.index()


class InstitutionStatisticsView(BaseStatisticsView):
    """Plausible dashboard of a single institution, for portal managers."""

    @property
    def site_id(self):
        return f"{plausible.get_plausible_site_domain()}/{self.context.getId()}"

    def get_stored_token(self):
        return getattr(self.context, "plausible_shared_link_token", None)

    def store_token(self, token):
        self.context.plausible_shared_link_token = token


class PlausibleStatisticsControlPanelView(BaseStatisticsView):
    """Global Plausible dashboard of the whole portal, for administrators."""

    label = _("Plausible statistics")

    @property
    def site_id(self):
        return plausible.get_plausible_site_domain()

    def get_stored_token(self):
        return api.portal.get_registry_record(PLAUSIBLE_TOKEN_REGISTRY_KEY, default=None)

    def store_token(self, token):
        api.portal.set_registry_record(PLAUSIBLE_TOKEN_REGISTRY_KEY, token)
