# -*- coding: utf-8 -*-

from plone import api
from plone.app.testing import applyProfile
from plone.app.testing import login
from plonemeeting.portal.core.testing import (
    PLONEMEETING_PORTAL_CORE_INTEGRATION_TESTING,
)  # noqa
from zope.component import queryUtility
from zope.schema.interfaces import IVocabularyFactory

import unittest


class TestMeetingWorkflow(unittest.TestCase):

    layer = PLONEMEETING_PORTAL_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.catalog = self.portal.portal_catalog

        self.portal.acl_users._doAddUser("manager", "secret", ["Manager"], [])

        applyProfile(self.portal, "plonemeeting.portal.core:demo")
        login(self.portal, "manager")
        city1 = getattr(self.portal, "amityville")
        brains = api.content.find(context=city1, portal_type="Meeting")
        self.meeting = brains[0].getObject()
        brains = api.content.find(context=self.meeting, portal_type="Item")
        self.meeting_item = brains[0].getObject()
        city2 = getattr(self.portal, "belleville")
        brains = api.content.find(context=city2, portal_type="Meeting")
        self.meeting2 = brains[0].getObject()
        brains = api.content.find(context=self.meeting2, portal_type="Item")
        self.meeting_item2 = brains[0].getObject()

    def testGlobalCategoryVocabulary(self):
        vocab = queryUtility(
            IVocabularyFactory, "plonemeeting.portal.vocabularies.global_categories"
        )
        values = vocab(self.meeting_item)
        self.assertEqual(len(values), 13)

    def testRepresentativesVocabulary(self):
        vocab = queryUtility(
            IVocabularyFactory, "plonemeeting.portal.vocabularies.representatives"
        )
        values_city1 = vocab(self.meeting_item)
        values_city2 = vocab(self.meeting_item2)
        self.assertFalse(len(values_city1) == len(values_city2))

    def testMeetingDatesVocabulary(self):
        vocab = queryUtility(
            IVocabularyFactory, "plonemeeting.portal.vocabularies.meeting_dates"
        )
        values_city1 = vocab(self.meeting_item)
        terms = [t for t in values_city1]
        self.assertEqual(terms[0].title, "13 March 2020 (18:00) — published")
        self.assertEqual(terms[1].title, "13 March 2019 (18:00) — published")
        self.assertEqual(terms[2].title, "20 December 2018 (18:25) — published")
