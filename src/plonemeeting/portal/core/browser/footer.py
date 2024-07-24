import os

from importlib_metadata import version, PackageNotFoundError

from Products.CMFCore.ActionInformation import ActionInfo
from Products.Five import BrowserView
from plone.memoize import forever
from plone import api


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
