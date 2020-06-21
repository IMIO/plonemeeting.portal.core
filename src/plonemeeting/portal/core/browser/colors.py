from Products.Five.browser import BrowserView
from plone import api

from plonemeeting.portal.core.content.institution import IInstitution


class ColorsCSSView(BrowserView):
    """
    Dynamic css generation for institution color customizations
    """

    CSS_TEMPLATE = u""":root {{
    --main-nav-color: {mainNavColor} !important;
    --main-nav-text-color: {mainNavTextColor} !important;
}}
    """

    def __call__(self, *args, **kwargs):
        self.request.response.setHeader("Content-type", "text/css")
        return self.render()

    def render(self):
        """
        Render the css with the institution colors
        """
        nav_root = api.portal.get_navigation_root(self.context)
        if IInstitution.providedBy(nav_root):
            css = self.CSS_TEMPLATE.format(
                mainNavColor=nav_root.nav_color,
                mainNavTextColor=nav_root.nav_text_color,
            )
            return css
        return ""
