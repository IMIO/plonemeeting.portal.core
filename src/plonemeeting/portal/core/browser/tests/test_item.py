# -*- coding: utf-8 -*-

from plonemeeting.portal.core.testing import PLONEMEETING_PORTAL_DEMO_FUNCTIONAL_TESTING
from plone.app.testing import login
from plone.app.testing import logout
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME

import unittest


class TestItemView(unittest.TestCase):
    layer = PLONEMEETING_PORTAL_DEMO_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        login(self.portal, TEST_USER_NAME)

    def tearDown(self):
        logout()

    def test_get_files(self):
        meeting = self.portal["belleville"]["16-novembre-2018-08-30"]
        item = meeting["approbation-du-pv-du-xxx"]
        files = item.restrictedTraverse("@@view").get_files()
        self.assertEqual(1, len(files))
        self.assertEqual(item["document.pdf"], files[0].getObject())
