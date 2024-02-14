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
        self.request.response.setHeader("Content-type", "text/css")
        # self.request.response.setHeader("Last-Modified", rfc1123_date(float(scripts_timestamp)))
        self.request.response.setHeader("Cache-Control", "max-age=31536000, public")
        return self.render()

    def render(self):
        """
        Render the css with the institution colors
        """
        portal = api.portal.get()
        institutions = [obj for obj in portal.objectValues() if obj.portal_type == "Institution"]
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
