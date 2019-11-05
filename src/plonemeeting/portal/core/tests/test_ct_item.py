# -*- coding: utf-8 -*-
from plonemeeting.portal.core.content.item import IItem  # NOQA E501
from plonemeeting.portal.core.testing import (
    PLONEMEETING_PORTAL_CORE_INTEGRATION_TESTING,
)  # noqa
from plone import api
from plone.api.exc import InvalidParameterError
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.dexterity.interfaces import IDexterityItem
from plone.dexterity.interfaces import IDexterityFTI
from zope.component import createObject
from zope.component import queryUtility

import unittest


class ItemIntegrationTest(unittest.TestCase):

    layer = PLONEMEETING_PORTAL_CORE_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        portal_types = self.portal.portal_types
        parent_id = portal_types.constructContent(
            "Meeting", self.portal, "parent_container", title="Parent container"
        )
        self.parent = self.portal[parent_id]

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
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
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
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        fti = queryUtility(IDexterityFTI, name="Item")
        self.assertFalse(fti.global_allow, u"{0} is globally addable!".format(fti.id))

    def test_ct_item_filter_content_type_true(self):
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        fti = queryUtility(IDexterityFTI, name="Item")
        portal_types = self.portal.portal_types
        parent_id = portal_types.constructContent(
            fti.id, self.portal, "item_id", title="Item container"
        )
        self.parent = self.portal[parent_id]
        with self.assertRaises(InvalidParameterError):
            api.content.create(
                container=self.parent, type="Document", title="My Content"
            )
