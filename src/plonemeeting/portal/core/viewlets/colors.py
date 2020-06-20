# -*- coding: utf-8 -*-
import json

from plone.app.layout.viewlets.common import ViewletBase
from plone import api

from plonemeeting.portal.core.content.institution import IInstitution


class PMColorsViewlet(ViewletBase):
    """
    Include some color settings in <head> section which initializes
    Javascript variables. This is used to customize colors at runtime for institutions
    """
    TEMPLATE = u"""
    <script type="text/javascript" class="javascript-settings">
         window.portalColors = {payload};
    </script>
    """

    def render(self):
        """
        Render the colors settings as inline Javascript object in HTML <head>
        """
        nav_root = api.portal.get_navigation_root(self.context)
        if IInstitution.providedBy(nav_root):
            color_settings = {
                "mainNavColor": nav_root.nav_color,
                "mainNavTextColor": nav_root.nav_text_color
            }
            html = self.TEMPLATE.format(payload=json.dumps(color_settings))
            return html
        return ''
