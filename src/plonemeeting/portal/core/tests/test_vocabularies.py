# -*- coding: utf-8 -*-

from plone import api

from plonemeeting.portal.core.tests.portal_test_case import (
    PmPortalDemoFunctionalTestCase,
)
from zope.component import queryUtility
from zope.schema.interfaces import IVocabularyFactory


class TestVocabularies(PmPortalDemoFunctionalTestCase):
    def setUp(self):
        super().setUp()
        self.catalog = self.portal.portal_catalog

        self.login_as_manager()
        city2 = getattr(self.portal, "belleville")
        brains = api.content.find(context=city2, portal_type="Meeting")
        self.meeting2 = brains[0].getObject()
        brains = api.content.find(context=self.meeting2, portal_type="Item")
        self.item2 = brains[0].getObject()

    def testGlobalCategoryVocabulary(self):
        vocab = queryUtility(
            IVocabularyFactory, "plonemeeting.portal.vocabularies.global_categories"
        )
        values = vocab(self.item)
        self.assertEqual(len(values), 29)

    def testRepresentativesVocabulary(self):
        vocab = queryUtility(
            IVocabularyFactory, "plonemeeting.portal.vocabularies.representatives"
        )
        voc = vocab(self.item)
        values_city1 = [term.title for term in voc._terms]
        self.assertListEqual(values_city1,
                             ['Mr DUPONT', 'Mr Dupuis', 'Mr Oniz', 'Mr Baka', 'Mr Kuro'])
        voc = vocab(self.item2)
        values_city2 = [term.title for term in voc._terms]
        self.assertListEqual(values_city2,
                             ['Mme LOREM', 'Mme Ipsum', 'Mr Wara', 'Mr Bara'])

    def testLongRepresentativesVocabulary(self):
        vocab = queryUtility(
            IVocabularyFactory, "plonemeeting.portal.vocabularies.long_representatives"
        )
        voc = vocab(self.item)
        values_city1 = [term.title for term in voc._terms]
        self.assertListEqual(values_city1,
                             ['Mr DUPONT Bourgmestre F.F.',
                              'Mr Dupuis 1ère Échevin',
                              "Mr Oniz, Échevin de l'éducation",
                              "Mr Baka, Échevin de des sports",
                              "Mr Kuro, Échevin de la culture"])
        voc = vocab(self.item2)
        values_city2 = [term.title for term in voc._terms]
        self.assertListEqual(values_city2,
                             ['Mme LOREM Bourgmestre',
                              'Mme Ipsum 1ère Échevine',
                              'Mr Wara, Échevin du tourisme',
                              'Mr Bara, Échevin du Développement économique'])

    def testMeetingDatesVocabulary(self):
        vocab = queryUtility(
            IVocabularyFactory, "plonemeeting.portal.vocabularies.meeting_dates"
        )
        values_city1 = vocab(self.item)
        terms = [t for t in values_city1]
        self.assertEqual(terms[0].title, "13 March 2020 (18:00) — decision")
        self.assertEqual(terms[1].title, "13 March 2019 (18:00) — decision")
        self.assertEqual(terms[2].title, "20 December 2018 (18:25) — decision")
