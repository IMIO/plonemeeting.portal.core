# -*- coding: utf-8 -*-

from plonemeeting.portal.core.testing import PLONEMEETING_PORTAL_DEMO_FUNCTIONAL_TESTING
from plone.app.testing import login
from plone.app.testing import logout
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.textfield.value import RichTextValue

import unittest


class TestItemView(unittest.TestCase):
    layer = PLONEMEETING_PORTAL_DEMO_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        login(self.portal, TEST_USER_NAME)
        self.meeting = self.portal["belleville"]["16-novembre-2018-08-30"]
        self.item = self.meeting["approbation-du-pv-du-xxx"]

    def tearDown(self):
        logout()

    def test_get_files(self):
        files = self.item.restrictedTraverse("@@view").get_files()
        self.assertEqual(1, len(files))
        self.assertEqual(self.item["document.pdf"], files[0].getObject())

    def test_title(self):
        self.assertEqual(self.item.formatted_title, None)
        self.assertEqual(self.item.title, "Approbation du PV du XXX")
        self.item.formatted_title = RichTextValue(
            "<p>test formatted title</p>", "text/html", "text/html"
        )
        self.assertEqual(self.item.title, "test formatted title")
