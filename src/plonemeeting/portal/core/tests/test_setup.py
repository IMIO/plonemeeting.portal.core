# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from plonemeeting.portal.core.testing import (
    PLONEMEETING_PORTAL_CORE_INTEGRATION_TESTING,
)  # noqa: E501
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID

import unittest


try:
    from Products.CMFPlone.utils import get_installer
except ImportError:
    get_installer = None


class TestSetup(unittest.TestCase):
    """Test that plonemeeting.portal.core is properly installed."""

    layer = PLONEMEETING_PORTAL_CORE_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
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


class TestUninstall(unittest.TestCase):

    layer = PLONEMEETING_PORTAL_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        if get_installer:
            self.installer = get_installer(self.portal, self.layer["request"])
        else:
            self.installer = api.portal.get_tool("portal_quickinstaller")
        roles_before = api.user.get_roles(TEST_USER_ID)
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.installer.uninstallProducts(["plonemeeting.portal.core"])
        setRoles(self.portal, TEST_USER_ID, roles_before)

    def test_product_uninstalled(self):
        """Test if plonemeeting.portal.core is cleanly uninstalled."""
        self.assertFalse(self.installer.is_product_installed("plonemeeting.portal.core"))

    def test_browserlayer_removed(self):
        """Test that IPlonemeetingPortalCoreLayer is removed."""
        from plonemeeting.portal.core.interfaces import IPlonemeetingPortalCoreLayer
        from plone.browserlayer import utils

        self.assertNotIn(IPlonemeetingPortalCoreLayer, utils.registered_layers())
