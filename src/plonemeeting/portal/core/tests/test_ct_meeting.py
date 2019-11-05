# -*- coding: utf-8 -*-
from plonemeeting.portal.core.content.meeting import IMeeting  # NOQA E501
from plonemeeting.portal.core.testing import (
    PLONEMEETING_PORTAL_CORE_INTEGRATION_TESTING,
)  # noqa
from plone import api
from plone.api.exc import InvalidParameterError
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.dexterity.interfaces import IDexterityFTI
from zope.component import createObject
from zope.component import queryUtility

import unittest


class MeetingIntegrationTest(unittest.TestCase):

    layer = PLONEMEETING_PORTAL_CORE_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        portal_types = self.portal.portal_types
        parent_id = portal_types.constructContent(
            "Institution", self.portal, "parent_container", title="Parent container",
        )
        self.parent = self.portal[parent_id]

    def test_ct_meeting_schema(self):
        fti = queryUtility(IDexterityFTI, name="Meeting")
        schema = fti.lookupSchema()
        self.assertEqual(IMeeting, schema)

    def test_ct_meeting_fti(self):
        fti = queryUtility(IDexterityFTI, name="Meeting")
        self.assertTrue(fti)

    def test_ct_meeting_factory(self):
        fti = queryUtility(IDexterityFTI, name="Meeting")
        factory = fti.factory
        obj = createObject(factory)

        self.assertTrue(
            IMeeting.providedBy(obj), u"IMeeting not provided by {0}!".format(obj,),
        )

    def test_ct_meeting_adding(self):
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        obj = api.content.create(container=self.parent, type="Meeting", id="meeting",)

        self.assertTrue(
            IMeeting.providedBy(obj), u"IMeeting not provided by {0}!".format(obj.id,),
        )

        parent = obj.__parent__
        self.assertIn("meeting", parent.objectIds())

        # check that deleting the object works too
        api.content.delete(obj=obj)
        self.assertNotIn("meeting", parent.objectIds())

    def test_ct_meeting_globally_not_addable(self):
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        fti = queryUtility(IDexterityFTI, name="Meeting")
        self.assertFalse(fti.global_allow, u"{0} is globally addable!".format(fti.id))

    def test_ct_meeting_filter_content_type_true(self):
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        fti = queryUtility(IDexterityFTI, name="Meeting")
        portal_types = self.portal.portal_types
        parent_id = portal_types.constructContent(
            fti.id, self.portal, "meeting_id", title="Meeting container",
        )
        self.parent = self.portal[parent_id]
        with self.assertRaises(InvalidParameterError):
            api.content.create(
                container=self.parent, type="Document", title="My Content",
            )
