# -*- coding: utf-8 -*-
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plonemeeting.portal.core.interfaces import IPlonemeetingPortalCoreLayer
from plonemeeting.portal.core.testing import PLONEMEETING_PORTAL_CORE_FUNCTIONAL_TESTING
from plonemeeting.portal.core.testing import PLONEMEETING_PORTAL_CORE_INTEGRATION_TESTING
from plonemeeting.portal.core.tests.portal_test_case import PmPortalDemoFunctionalTestCase
from Products.Five.browser import BrowserView
from zope.component import queryMultiAdapter
from zope.interface import alsoProvides
from zope.viewlet.interfaces import IViewletManager

import unittest


class ViewletsIntegrationTest(PmPortalDemoFunctionalTestCase):

    layer = PLONEMEETING_PORTAL_CORE_INTEGRATION_TESTING

    def setUp(self):
        super().setUp()
        self.institution.webstats_js = """
            <script>https://nohost/tracking.js</script>
        """

    def test_tracking_viewlet_is_registered(self):
        view = BrowserView(self.portal['other-document'], self.request)
        manager_name = 'plone.abovecontenttitle'
        alsoProvides(self.request, IPlonemeetingPortalCoreLayer)
        manager = queryMultiAdapter(
            (self.meeting, self.request, view),
            IViewletManager,
            manager_name,
            default=None
        )
        self.assertIsNotNone(manager)
        manager.update()
        my_viewlet = [v for v in manager.viewlets if v.__name__ == 'tracking-viewlet']  # NOQA: E501
        self.assertEqual(len(my_viewlet), 1)


class ViewletFunctionalTest(unittest.TestCase):

    layer = PLONEMEETING_PORTAL_CORE_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
