# -*- coding: utf-8 -*-
from plone import api
from Products.Five.browser import BrowserView
from zope.datetime import rfc1123_date


class ColorsCSSView(BrowserView):
    """
    Dynamic css generation for institution color customizations
    """

    CSS_TEMPLATE = u"""
.site-{institution_id} {{
    --header-color: {header_color} !important;
    --nav-color: {main_nav_color} !important;
    --nav-text-color: {main_nav_text_color} !important;
    --links-color: {links_color} !important;
    --footer-color: {footer_color} !important;
    --footer-text-color: {footer_text_color} !important;
}}
"""

    def __call__(self, *args, **kwargs):
        institutions = self._get_institutions()
        self.request.response.setHeader("Content-type", "text/css")
        last_modified = self._get_last_modified(institutions)
        if last_modified is not None:
            self.request.response.setHeader("Last-Modified", rfc1123_date(last_modified))
        self.request.response.setHeader("Cache-Control", "max-age=31536000, public")
        return self.render(institutions)

    def _get_institutions(self):
        portal = api.portal.get()
        return [obj for obj in portal.objectValues() if obj.portal_type == "Institution"]

    def _get_last_modified(self, institutions):
        """Most recent institution modification date, as epoch seconds, or None"""
        times = [inst.modified().timeTime() for inst in institutions if inst.modified()]
        return max(times) if times else None

    def render(self, institutions=None):
        """
        Render the css with the institution colors
        """
        if institutions is None:
            institutions = self._get_institutions()
        css = " "
        for institution in institutions:
            css += self.CSS_TEMPLATE.format(
                institution_id=institution.id,
                header_color=institution.header_color,
                main_nav_color=institution.nav_color,
                main_nav_text_color=institution.nav_text_color,
                links_color=institution.links_color,
                footer_color=institution.footer_color,
                footer_text_color=institution.footer_text_color,
            )
        return css
