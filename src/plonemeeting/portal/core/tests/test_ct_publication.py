# -*- coding: utf-8 -*-
from plone import api
from plone.api.exc import InvalidParameterError
from plone.dexterity.interfaces import IDexterityFTI
from plonemeeting.portal.core.config import PUB_FOLDER_ID
from plonemeeting.portal.core.content.publication import IPublication
from plonemeeting.portal.core.tests.portal_test_case import PmPortalTestCase
from zope.component import createObject
from zope.component import queryUtility


class PublicationIntegrationTest(PmPortalTestCase):
    def test_ct_publication_schema(self):
        fti = queryUtility(IDexterityFTI, name="Publication")
        schema = fti.lookupSchema()
        self.assertEqual(IPublication, schema)

    def test_ct_publication_fti(self):
        fti = queryUtility(IDexterityFTI, name="Publication")
        self.assertTrue(fti)

    def test_ct_publication_factory(self):
        fti = queryUtility(IDexterityFTI, name="Publication")
        factory = fti.factory
        obj = createObject(factory)

        self.assertTrue(
            IPublication.providedBy(obj),
            msg=u"IPublication not provided by {0}!".format(obj),
        )

    def test_ct_publication_adding(self):
        self.login_as_admin()

        with self.assertRaises(InvalidParameterError):
            # Cannot create a publication at the portal root
            api.content.create(
                container=self.portal, type="Publication", id="publication-test"
            )

        institution = api.content.create(
            container=self.portal, type="Institution", id="institution"
        )
        self.assertEqual(len(institution[PUB_FOLDER_ID]), 0)
        api.content.create(
            container=institution.publications, type="Publication", id="publication-test"
        )
        self.assertEqual(len(institution[PUB_FOLDER_ID]), 1)


    def test_ct_publication_globally_not_addable(self):
        self.login_as_admin()
        fti = queryUtility(IDexterityFTI, name="Publication")
        self.assertFalse(fti.global_allow, u"{0} is globally addable!".format(fti.id))
