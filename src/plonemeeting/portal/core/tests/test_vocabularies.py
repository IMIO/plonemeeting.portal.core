# -*- coding: utf-8 -*-
from mockito import mock
from mockito import unstub
from mockito import verify
from mockito import when
from plone import api
from plonemeeting.portal.core.config import API_HEADERS
from plonemeeting.portal.core.config import DOCUMENTGENENATOR_USED_CONTENT_TYPES
from plonemeeting.portal.core.config import DOCUMENTGENERATOR_GENERABLE_CONTENT_TYPES
from plonemeeting.portal.core.tests.portal_test_case import PmPortalDemoFunctionalTestCase
from plonemeeting.portal.core.utils import get_api_url_for_meetings
from zope.component import queryUtility
from zope.i18n import translate
from zope.schema.interfaces import IVocabularyFactory

import json
import requests


class TestVocabularies(PmPortalDemoFunctionalTestCase):
    def setUp(self):
        super().setUp()
        self.login_as_admin()
        city2 = getattr(self.portal, "belleville")
        brains = api.content.find(context=city2, portal_type="Meeting")
        self.meeting2 = brains[0].getObject()
        brains = api.content.find(context=self.meeting2, portal_type="Item")
        self.item2 = brains[0].getObject()

    def testLocalCategoryVocabulary(self):
        belleville = self.portal["belleville"]
        vocab = queryUtility(
            IVocabularyFactory, "plonemeeting.portal.vocabularies.local_categories"
        )
        self.portal.REQUEST.set('PUBLISHED', belleville.restrictedTraverse("@@edit"))
        values = vocab(belleville)
        self.assertEqual(len(values), 29)

        values = vocab({"test": 'yolo'})
        self.assertEqual(len(values), 29)

        belleville.delib_categories = {"admin": "Administrative", "political": "Political"}
        values = vocab({"test": 'yolo'})
        self.assertEqual(len(values), 29)
        values = vocab(belleville)
        self.assertEqual(len(values), 2)

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
        self.institution.representatives_mappings[2]['active'] = False
        self.institution.representatives_mappings[4]['active'] = False
        voc = vocab(self.item)
        values_city1 = [translate(term.title) for term in voc._terms]
        self.assertListEqual(values_city1,
                             ['Mr DUPONT', 'Mr Dupuis', 'Mr Baka',
                              '(Passed term of office) Mr Oniz', '(Passed term of office) Mr Kuro'])
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
        self.institution.representatives_mappings[2]['active'] = False
        self.institution.representatives_mappings[4]['active'] = False
        voc = vocab(self.item)
        values_city1 = [translate(term.title) for term in voc._terms]
        self.assertListEqual(values_city1,
                             ['Mr DUPONT Bourgmestre F.F.', 'Mr Dupuis 1ère Échevin', 'Mr Baka, Échevin de des sports',
                              "(Passed term of office) Mr Oniz, Échevin de l'éducation",
                              '(Passed term of office) Mr Kuro, Échevin de la culture'])
        voc = vocab(self.item2)
        values_city2 = [term.title for term in voc._terms]
        self.assertListEqual(values_city2,
                             ['Mme LOREM Bourgmestre',
                              'Mme Ipsum 1ère Échevine',
                              'Mr Wara, Échevin du tourisme',
                              'Mr Bara, Échevin du Développement économique'])

    def testRemoteMeetingsVocabulary(self):
        vocab = queryUtility(
            IVocabularyFactory, "plonemeeting.portal.vocabularies.remote_meetings"
        )
        url = get_api_url_for_meetings(self.institution)
        meetings = {
            "items": [
                {"UID": "uid1", "title": "Meeting 1"},
                {"UID": "uid2", "title": "Meeting 2"},
            ]
        }
        when(requests).get(
            url,
            auth=(self.institution.username, self.institution.password),
            headers=API_HEADERS,
        ).thenReturn(mock({"status_code": 200, "text": json.dumps(meetings)}))

        values = vocab(self.institution)
        titles = [term.title for term in values]
        self.assertListEqual(titles, ["Meeting 1", "Meeting 2"])
        verify(requests, times=1).get(
            url,
            auth=(self.institution.username, self.institution.password),
            headers=API_HEADERS,
        )

    def testRemoteMeetingsVocabularyAPIFailure(self):
        vocab = queryUtility(
            IVocabularyFactory, "plonemeeting.portal.vocabularies.remote_meetings"
        )
        url = get_api_url_for_meetings(self.institution)
        when(requests).get(
            url,
            auth=(self.institution.username, self.institution.password),
            headers=API_HEADERS,
        ).thenReturn(mock({"status_code": 404, "text": ""}))

        values = vocab(self.institution)
        self.assertEqual(len(values), 0)
        verify(requests, times=1).get(
            url,
            auth=(self.institution.username, self.institution.password),
            headers=API_HEADERS,
        )

    def testMeetingDatesVocabulary(self):
        vocab = queryUtility(
            IVocabularyFactory, "plonemeeting.portal.vocabularies.meeting_dates"
        )
        values_city1 = vocab(self.item)
        terms = [t for t in values_city1]
        self.assertEqual(terms[0].title, "13 March 2020 (18:00) — decision")
        self.assertEqual(terms[1].title, "13 March 2019 (18:00) — decision")
        self.assertEqual(terms[2].title, "20 December 2018 (18:25) — decision")

    def testPodTemplatesTypesVocabulary(self):
        vocab = queryUtility(
            IVocabularyFactory, "collective.documentgenerator.PortalTypes"
        )
        values = vocab(self.item)
        titles = [term.title for term in values]
        self.assertListEqual(titles, DOCUMENTGENERATOR_GENERABLE_CONTENT_TYPES)
