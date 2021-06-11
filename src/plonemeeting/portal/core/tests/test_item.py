# -*- coding: utf-8 -*-
from imio.helpers.content import richtextval
from plonemeeting.portal.core.content.item import get_pretty_representatives
from plonemeeting.portal.core.tests.portal_test_case import (
    PmPortalDemoFunctionalTestCase,
)


class TestItemView(PmPortalDemoFunctionalTestCase):
    def setUp(self):
        super().setUp()
        self.institution = self.portal["belleville"]
        self.meeting = self.institution["16-novembre-2018-08-30"]
        self.item = self.meeting["approbation-du-pv-du-xxx"]
        self.login_as_test()

    def test_get_files(self):
        files = self.item.restrictedTraverse("@@view").get_files()
        self.assertEqual(1, len(files))
        self.assertEqual(self.item["document.pdf"], files[0].getObject())

    def test_title(self):
        self.assertEqual(self.item.formatted_title, None)
        self.assertEqual(self.item.title, "Approbation du PV du XXX")
        self.item.formatted_title = richtextval("<p>test formatted title</p>")
        self.assertEqual(self.item.title, "test formatted title")

    def test_get_pretty_representatives(self):
        self.assertEqual(get_pretty_representatives(self.item)(), 'Mme LOREM')

        self.item.representatives_in_charge = ['Yololololo-lolo-lolololo']
        self.assertRaises(AttributeError, get_pretty_representatives(self.item))

        self.item.representatives_in_charge = ['12c8f011-e164-40c8-914b-f4f11b440ae8',
                                               '381864c8-dc18-4a52-962c-8d0c677d3d3d',
                                               '8388cf29-6f4b-4910-b8fd-7be5e14f5175',
                                               '39d90590-a112-436a-80ff-d96c2082a553']
        self.assertEqual(get_pretty_representatives(self.item)(),
                         'Mme Ipsum, Mme LOREM, Mr Bara, Mr Wara')

        self.item.representatives_in_charge = ['39d90590-a112-436a-80ff-d96c2082a553',
                                               '381864c8-dc18-4a52-962c-8d0c677d3d3d',
                                               '12c8f011-e164-40c8-914b-f4f11b440ae8',
                                               '381864c8-dc18-4a52-962c-8d0c677d3d3d',
                                               '8388cf29-6f4b-4910-b8fd-7be5e14f5175',
                                               '39d90590-a112-436a-80ff-d96c2082a553']
        self.assertEqual(get_pretty_representatives(self.item)(),
                         'Mr Wara, Mme LOREM, Mme Ipsum, Mr Bara')
