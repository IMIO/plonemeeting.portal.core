# -*- coding: utf-8 -*-
from plone import api
from plone.dexterity.interfaces import IDexterityFTI
from plonemeeting.portal.core.content.item import IItem  # NOQA E501
from plonemeeting.portal.core.tests.portal_test_case import PmPortalTestCase
from zope.component import createObject
from zope.component import queryUtility


class ItemIntegrationTest(PmPortalTestCase):
    def setUp(self):
        """Custom shared utility setup for tests."""
        super().setUp()
        self.parent = self.create_object("Meeting")

    def test_ct_item_schema(self):
        fti = queryUtility(IDexterityFTI, name="Item")
        schema = fti.lookupSchema()
        self.assertEqual(IItem, schema)

    def test_ct_item_fti(self):
        fti = queryUtility(IDexterityFTI, name="Item")
        self.assertTrue(fti)

    def test_ct_item_factory(self):
        fti = queryUtility(IDexterityFTI, name="Item")
        factory = fti.factory
        obj = createObject(factory)

        self.assertTrue(
            IItem.providedBy(obj), u"IItem not provided by {0}!".format(obj)
        )

    def test_ct_item_adding(self):
        self.login_as_admin()
        obj = api.content.create(container=self.parent, type="Item", id="item")

        self.assertTrue(
            IItem.providedBy(obj), u"IItem not provided by {0}!".format(obj.id)
        )

        parent = obj.__parent__
        self.assertIn("item", parent.objectIds())

        # check that deleting the object works too
        api.content.delete(obj=obj)
        self.assertNotIn("item", parent.objectIds())

    def test_ct_item_globally_not_addable(self):
        self.login_as_admin()
        fti = queryUtility(IDexterityFTI, name="Item")
        self.assertFalse(fti.global_allow, u"{0} is globally addable!".format(fti.id))
