# -*- coding: utf-8 -*-
from plonemeeting.portal.core.content.institution import IInstitution
from plonemeeting.portal.core.testing import (
    PLONEMEETING_PORTAL_CORE_INTEGRATION_TESTING,
)  # noqa
from plonemeeting.portal.core.utils import format_institution_managers_group_id
from plone import api
from plone.api.exc import InvalidParameterError
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.dexterity.interfaces import IDexterityFTI
from zope.component import createObject
from zope.component import queryUtility

import unittest


class InstitutionIntegrationTest(unittest.TestCase):

    layer = PLONEMEETING_PORTAL_CORE_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.parent = self.portal

    def test_ct_institution_schema(self):
        fti = queryUtility(IDexterityFTI, name="Institution")
        schema = fti.lookupSchema()
        self.assertEqual(IInstitution, schema)

    def test_ct_institution_fti(self):
        fti = queryUtility(IDexterityFTI, name="Institution")
        self.assertTrue(fti)

    def test_ct_institution_factory(self):
        fti = queryUtility(IDexterityFTI, name="Institution")
        factory = fti.factory
        obj = createObject(factory)

        self.assertTrue(
            IInstitution.providedBy(obj),
            u"IInstitution not provided by {0}!".format(obj),
        )

    def test_ct_institution_adding(self):
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        obj = api.content.create(
            container=self.portal, type="Institution", id="institution"
        )

        group_id = format_institution_managers_group_id(obj)
        roles = api.group.get_roles(groupname=group_id)
        self.assertEqual(roles, ["Authenticated"])
        self.assertTupleEqual(
            obj.get_local_roles_for_userid(group_id),
            ("Institution Manager", "Contributor"),
        )

        self.assertTrue(
            IInstitution.providedBy(obj),
            u"IInstitution not provided by {0}!".format(obj.id),
        )

        parent = obj.__parent__
        self.assertIn("institution", parent.objectIds())

        # check that deleting the object works too
        api.content.delete(obj=obj)
        self.assertNotIn("institution", parent.objectIds())
        self.assertIsNone(api.group.get(group_id))

    def test_ct_institution_globally_addable(self):
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        fti = queryUtility(IDexterityFTI, name="Institution")
        self.assertTrue(
            fti.global_allow, u"{0} is not globally addable!".format(fti.id)
        )

    def test_ct_institution_filter_content_type_true(self):
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        fti = queryUtility(IDexterityFTI, name="Institution")
        portal_types = self.portal.portal_types
        parent_id = portal_types.constructContent(
            fti.id, self.portal, "institution_id", title="Institution container"
        )
        self.parent = self.portal[parent_id]
        with self.assertRaises(InvalidParameterError):
            api.content.create(
                container=self.parent, type="Document", title="My Content"
            )
