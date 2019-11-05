# -*- coding: utf-8 -*-
from plonemeeting.portal.core.content.annex import IAnnex  # NOQA E501
from plonemeeting.portal.core.testing import PLONEMEETING_PORTAL_CORE_INTEGRATION_TESTING  # noqa
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.dexterity.interfaces import IDexterityFTI
from zope.component import createObject
from zope.component import queryUtility

import unittest




class AnnexIntegrationTest(unittest.TestCase):

    layer = PLONEMEETING_PORTAL_CORE_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        portal_types = self.portal.portal_types
        parent_id = portal_types.constructContent(
            'Item',
            self.portal,
            'parent_container',
            title='Parent container',
        )
        self.parent = self.portal[parent_id]

    def test_ct_annex_schema(self):
        fti = queryUtility(IDexterityFTI, name='Annex')
        schema = fti.lookupSchema()
        self.assertEqual(IAnnex, schema)

    def test_ct_annex_fti(self):
        fti = queryUtility(IDexterityFTI, name='Annex')
        self.assertTrue(fti)

    def test_ct_annex_factory(self):
        fti = queryUtility(IDexterityFTI, name='Annex')
        factory = fti.factory
        obj = createObject(factory)

        self.assertTrue(
            IAnnex.providedBy(obj),
            u'IAnnex not provided by {0}!'.format(
                obj,
            ),
        )

    def test_ct_annex_adding(self):
        setRoles(self.portal, TEST_USER_ID, ['Contributor'])
        obj = api.content.create(
            container=self.parent,
            type='Annex',
            id='annex',
        )

        self.assertTrue(
            IAnnex.providedBy(obj),
            u'IAnnex not provided by {0}!'.format(
                obj.id,
            ),
        )

        parent = obj.__parent__
        self.assertIn('annex', parent.objectIds())

        # check that deleting the object works too
        api.content.delete(obj=obj)
        self.assertNotIn('annex', parent.objectIds())

    def test_ct_annex_globally_not_addable(self):
        setRoles(self.portal, TEST_USER_ID, ['Contributor'])
        fti = queryUtility(IDexterityFTI, name='Annex')
        self.assertFalse(
            fti.global_allow,
            u'{0} is globally addable!'.format(fti.id)
        )
