# -*- coding: utf-8 -*-

from plone import api
from plone.registry.interfaces import IRegistry
from plone.testing.zope import Browser
from plonemeeting.portal.core.content.institution import IInstitution
from plonemeeting.portal.core.tests.portal_test_case import PmPortalDemoFunctionalTestCase
from plonemeeting.portal.core.widgets.colorselect import ColorSelectFieldWidget
from Products.CMFPlone.interfaces import IBundleRegistry
from zope.component import getUtility
from zope.lifecycleevent import ObjectAddedEvent
from zope.lifecycleevent import ObjectModifiedEvent
from zope.schema import getFields

import zope.event


class TestColorCSSView(PmPortalDemoFunctionalTestCase):
    def setUp(self):
        super().setUp()
        self.institution: IInstitution = self.portal["belleville"]
        self.institution.header_color = "#FFFFFF"
        self.institution.nav_color = "#EEEEEEE"
        self.institution.nav_text_color = "#DDDDDD"
        self.institution.links_color = "#CCCCCC"
        self.institution.footer_color = "#BBBBBB"
        self.institution.footer_text_color = "#AAAAAA"

    def test_render_custom_css(self):
        """ Test if the custom colors CSS generation view render the correct color values"""
        view_content = api.portal.get().unrestrictedTraverse("@@custom_colors.css")()

        self.assertIn("--header-color: #FFFFFF", view_content)
        self.assertIn("--nav-color: #EEEEEEE", view_content)
        self.assertIn("--nav-text-color: #DDDDDD", view_content)
        self.assertIn("--links-color: #CCCCCC", view_content)
        self.assertIn("--footer-color: #BBBBBB", view_content)
        self.assertIn("--footer-text-color: #AAAAAA", view_content)

    def test_custom_css_is_served_correctly_to_the_browser(self):
        """ Test all of custom colors css """
        app = self.layer["app"]
        browser = Browser(app)
        browser.open(self._get_css_absolute_url())
        old_custom_colors_css = browser.contents

        self.institution.header_color = "#ABABAB"
        self._fire_event(self.institution, "modified")

        import transaction

        transaction.commit()  # Commit so that the test browser sees these changes

        browser.open(self._get_css_absolute_url())
        new_custom_colors_css = browser.contents

        self.assertNotEqual(old_custom_colors_css, new_custom_colors_css)
        self.assertIn("--header-color: #ABABAB", new_custom_colors_css)

    def test_color_select_widget_render(self):
        """ Test if the color select widget render a correct input type """
        header_color_field = getFields(IInstitution)["header_color"]
        color_select_render = ColorSelectFieldWidget(
            header_color_field, self.portal.REQUEST
        ).render()
        self.assertIn("""<input type="color" id="header_color""", color_select_render)

    def _get_bundle(self) -> IBundleRegistry:
        """Get the bundle registry entry for the custom colors css"""
        registry = getUtility(IRegistry)
        bundles = registry.collectionOfInterface(
            IBundleRegistry, prefix="plone.bundles", check=False
        )
        return bundles.get("plonemeeting.portal.core-custom")

    # def _get_bundle_content(self) -> str:
    #     """Get the custom colors css directly from plone_resources"""
    #     overrides = OverrideFolderManager(self.institution)
    #     css_file_name = self._get_bundle().csscompilation.replace(
    #         "++plone++static/", ""
    #     )
    #     with overrides.container["static"].openFile(css_file_name) as file:
    #         content = str(file.read(), "utf-8")
    #     return content

    def _get_css_absolute_url(self) -> str:
        """Get the custom colors css path"""
        return "{0}/{1}".format(
            self.portal.absolute_url(), self._get_bundle().csscompilation
        )

    def _fire_event(self, context, event):
        if event == "modified":
            event = ObjectModifiedEvent(context)
        elif event == "added":
            event = ObjectAddedEvent(context)
        if event:
            zope.event.notify(event)
