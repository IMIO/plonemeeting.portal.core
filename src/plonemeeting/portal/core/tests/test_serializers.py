# -*- coding: utf-8 -*-
from plone import api
from plonemeeting.portal.core.interfaces import IInstitutionSerializeToJson
from plonemeeting.portal.core.tests.portal_test_case import PmPortalTestCase
from zope.component import queryMultiAdapter


class TestSerializers(PmPortalTestCase):

    def test_institution_serializer(self):
        institution = api.content.create(
            container=self.portal, type="Institution", id="institution", title="Gotham City"
        )
        request = self.portal.REQUEST
        serializer = queryMultiAdapter((institution, request), IInstitutionSerializeToJson)
        result = serializer(fieldnames=["title"])
        self.assertIn("title", result.keys())
        self.assertNotIn("plonemeeting_url", result.keys())
        self.assertEqual(result["title"], "Gotham City")

        institution.meeting_type = "council"
        result = serializer(fieldnames=["title", "meeting_type"])
        self.assertIn("meeting_type", result.keys())
        self.assertEqual(result["meeting_type"]["token"], "council")
        self.assertEqual(result["meeting_type"]["title"], "Séance publique du Conseil")

        institution.meeting_filter_query = [{'parameter': 'review_state', 'value': 'created'}]
        result = serializer(fieldnames=["meeting_filter_query"])
        self.assertIn("meeting_filter_query", result.keys())
        self.assertDictEqual(result["meeting_filter_query"][0], {'parameter': 'review_state', 'value': 'created'})

        result = serializer(fieldnames=["non_existing_field"])
        self.assertNotIn("non_existing_field", result.keys())
