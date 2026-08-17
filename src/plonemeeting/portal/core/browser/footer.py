from importlib_metadata import PackageNotFoundError
from importlib_metadata import version
from plone import api
from plone.memoize import forever
from plonemeeting.portal.core.content.institution import IInstitution
from plonemeeting.portal.core.oidc import get_login_url
from Products.CMFCore.ActionInformation import ActionInfo
from Products.Five import BrowserView
from urllib.parse import quote

import os


class FooterView(BrowserView):
    """Footer view"""

    def __init__(self, context, request):
        super().__init__(context, request)
        self.portal_actions = api.portal.get_tool('portal_actions')

    def get_site_actions(self):
        actions = self.portal_actions.listActions(categories=['site_actions'])
        ec = self.portal_actions._getExprContext(self.context)
        actions = [ActionInfo(action, ec) for action in actions]
        return actions

    def login_url(self):
        """Where the footer's "Log in" link points.

        Inside an institution the link follows the institution's
        authentication method: straight to the OIDC (Keycloak) flow when SSO
        is selected, the classic Plone login form otherwise.  On the portal
        home page the visitor is sent to an intermediate page to choose
        between the two systems.  When OIDC is not configured everything
        degrades to the classic login form.
        """
        nav_root = api.portal.get_navigation_root(self.context)
        root_url = nav_root.absolute_url()
        came_from = self.request.get("ACTUAL_URL", "")
        if IInstitution.providedBy(nav_root):
            if getattr(nav_root, "authentication", "plone") == "oidc":
                oidc_url = get_login_url(came_from=came_from)
                if oidc_url:
                    return oidc_url
            return f"{root_url}/login"
        if get_login_url() is None:
            return f"{root_url}/login"
        url = f"{root_url}/@@login-choice"
        if came_from:
            url = f"{url}?came_from={quote(came_from)}"
        return url

    def get_social_actions(self):
        actions = self.portal_actions.listActions(categories=['site_socials'])
        ec = self.portal_actions._getExprContext(self.context)
        actions = [ActionInfo(action, ec) for action in actions]
        return actions

    @forever.memoize
    def get_version(self):
        """Get the application version"""
        try:
            return version("plonemeeting.portal.core")
        except PackageNotFoundError:
            return ""

    @forever.memoize
    def get_build(self):
        """Get the build number"""
        if os.path.exists(".build_number"):
            with open(".build_number") as f:
                return "build " + f.read().strip()
