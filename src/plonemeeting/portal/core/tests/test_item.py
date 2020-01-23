# -*- coding: utf-8 -*-

from plone.app.textfield.value import RichTextValue

from plonemeeting.portal.core.tests.portal_test_case import PmPortalDemoFunctionalTestCase


class TestItemView(PmPortalDemoFunctionalTestCase):

    def setUp(self):
        super().setUp()
        self.meeting = self.portal["belleville"]["16-novembre-2018-08-30"]
        self.item = self.meeting["approbation-du-pv-du-xxx"]
        self.login_as_test()

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
