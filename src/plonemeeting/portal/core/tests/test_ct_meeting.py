# -*- coding: utf-8 -*-
from plone import api
from plone.api.exc import InvalidParameterError
from plone.dexterity.interfaces import IDexterityFTI
from plonemeeting.portal.core.content.meeting import IMeeting  # NOQA E501
from plonemeeting.portal.core.tests.portal_test_case import PmPortalTestCase
from zope.component import createObject
from zope.component import queryUtility


class MeetingIntegrationTest(PmPortalTestCase):
    def setUp(self):
        """Custom shared utility setup for tests."""
        super().setUp()
        self.institution = self.create_object("Institution")

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
            IMeeting.providedBy(obj), u"IMeeting not provided by {0}!".format(obj)
        )

    def test_ct_meeting_adding(self):
        self.login_as_admin()
        decisions = self.institution.decisions
        obj = api.content.create(container=decisions, type="Meeting", id="meeting")

        self.assertTrue(
            IMeeting.providedBy(obj), u"IMeeting not provided by {0}!".format(obj.id)
        )

        self.assertIn("meeting", decisions.objectIds())

        # check that deleting the object works too
        api.content.delete(obj=obj)
        self.assertNotIn("meeting", decisions.objectIds())

    def test_ct_meeting_globally_not_addable(self):
        self.login_as_admin()
        fti = queryUtility(IDexterityFTI, name="Meeting")
        self.assertFalse(fti.global_allow, u"{0} is globally addable!".format(fti.id))

    def test_ct_meeting_filter_content_type_true(self):
        self.login_as_admin()
        fti = queryUtility(IDexterityFTI, name="Meeting")
        portal_types = self.portal.portal_types
        parent_id = portal_types.constructContent(
            fti.id, self.portal, "meeting_id", title="Meeting container"
        )
        self.parent = self.portal[parent_id]
        with self.assertRaises(InvalidParameterError):
            api.content.create(
                container=self.parent, type="Document", title="My Content"
            )
