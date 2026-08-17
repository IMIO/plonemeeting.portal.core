# -*- coding: utf-8 -*-
from plone import api
from plonemeeting.portal.core.oidc import get_login_url
from Products.Five import BrowserView
from urllib.parse import quote


class LoginChoiceView(BrowserView):
    """Intermediate page shown on the portal home page: the visitor chooses
    between the classic Plone login and the SSO (OIDC) one.

    When OIDC is not configured there is nothing to choose from, so the view
    redirects straight to the classic login form.
    """

    @property
    def came_from(self):
        return self.request.get("came_from", "")

    def sso_login_url(self):
        return get_login_url(came_from=self.came_from or None)

    def local_login_url(self):
        url = f"{api.portal.get_navigation_root(self.context).absolute_url()}/login"
        if self.came_from:
            url = f"{url}?came_from={quote(self.came_from)}"
        return url

    def __call__(self):
        if self.sso_login_url() is None:
            self.request.response.redirect(self.local_login_url())
            return ""
        return self.index()
