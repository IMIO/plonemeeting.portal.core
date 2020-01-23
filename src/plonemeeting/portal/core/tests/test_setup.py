# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from plone import api

from plonemeeting.portal.core.tests.portal_test_case import PmPortalTestCase

try:
    from Products.CMFPlone.utils import get_installer
except ImportError:
    get_installer = None


class TestSetup(PmPortalTestCase):
    """Test that plonemeeting.portal.core is properly installed."""

    def setUp(self):
        """Custom shared utility setup for tests."""
        super().setUp()
        if get_installer:
            self.installer = get_installer(self.portal, self.layer["request"])
        else:
            self.installer = api.portal.get_tool("portal_quickinstaller")

    def test_product_installed(self):
        """Test if plonemeeting.portal.core is installed."""
        self.assertTrue(self.installer.is_product_installed("plonemeeting.portal.core"))

    def test_browserlayer(self):
        """Test that IPlonemeetingPortalCoreLayer is registered."""
        from plonemeeting.portal.core.interfaces import IPlonemeetingPortalCoreLayer
        from plone.browserlayer import utils

        self.assertIn(IPlonemeetingPortalCoreLayer, utils.registered_layers())


class TestUninstall(PmPortalTestCase):

    def setUp(self):
        super().setUp()
        if get_installer:
            self.installer = get_installer(self.portal, self.layer["request"])
        else:
            self.installer = api.portal.get_tool("portal_quickinstaller")
        self.installer.uninstallProducts(["plonemeeting.portal.core"])
        self.login_as_test()

    def test_product_uninstalled(self):
        """Test if plonemeeting.portal.core is cleanly uninstalled."""
        self.assertFalse(
            self.installer.is_product_installed("plonemeeting.portal.core")
        )

    def test_browserlayer_removed(self):
        """Test that IPlonemeetingPortalCoreLayer is removed."""
        from plonemeeting.portal.core.interfaces import IPlonemeetingPortalCoreLayer
        from plone.browserlayer import utils

        self.assertNotIn(IPlonemeetingPortalCoreLayer, utils.registered_layers())
