# -*- coding: utf-8 -*-
from datetime import datetime

from plone.app.testing import logout

from Products.CMFPlone.interfaces.constrains import ISelectableConstrainTypes
from eea.facetednavigation.interfaces import IFacetedNavigable
from plone import api
from plonemeeting.portal.core import utils
from plonemeeting.portal.core.tests.portal_test_case import PmPortalDemoFunctionalTestCase
from plonemeeting.portal.core.utils import format_meeting_date_and_state


class TestUtils(PmPortalDemoFunctionalTestCase):

    def setUp(self):
        super().setUp()
        self.belleville = self.portal["belleville"]
        self.login_as_manager()

    def tearDown(self):
        if "test-faceted" in self.portal:
            api.content.delete(self.portal["test-faceted"])
        logout()

    def test_get_api_url_for_meetings_missing_config(self):
        institution = type(
            "institution",
            (object,),
            {"plonemeeting_url": None, "meeting_config_id": None},
        )()
        self.assertIsNone(utils.get_api_url_for_meetings(institution))
        institution = type(
            "institution",
            (object,),
            {"plonemeeting_url": "foo", "meeting_config_id": None},
        )()
        self.assertIsNone(utils.get_api_url_for_meetings(institution))

    def test_get_api_url_for_meetings_by_UID(self):
        url = utils.get_api_url_for_meetings(self.belleville, meeting_UID="foo")
        self.assertEqual(
            "https://demo-pm.imio.be/@search_meetings?getConfigId="
            "meeting-config-college&UID=foo&fullobjects=True&b_size=9999",
            url,
        )

    def test_get_api_url_for_meetings_additional_query(self):
        url = utils.get_api_url_for_meetings(self.belleville)
        self.assertEqual(
            "https://demo-pm.imio.be/@search_meetings?"
            "getConfigId=meeting-config-college&review_state=frozen",
            url,
        )

    def test_get_api_url_for_meeting_items(self):
        url = utils.get_api_url_for_meeting_items(self.belleville, "foo")
        self.assertEqual(
            "https://demo-pm.imio.be/@search_items?sort_on=getItemNumber&privacy=public"
            "&privacy=public_heading&b_size=9999"
            "&getConfigId=meeting-config-college&linkedMeetingUID=foo&fullobjects=True"
            "&review_state=itemfrozen&review_state=accepted&review_state=accepted_but_modified",
            url,
        )

    def test_get_api_url_for_meeting_items_missing_config(self):
        institution = type(
            "institution",
            (object,),
            {"plonemeeting_url": None, "meeting_config_id": None},
        )()
        self.assertIsNone(utils.get_api_url_for_meeting_items(institution, "foo"))
        institution = type(
            "institution",
            (object,),
            {"plonemeeting_url": "foo", "meeting_config_id": None},
        )()
        self.assertIsNone(utils.get_api_url_for_meeting_items(institution, "foo"))

    def test_create_faceted_folder(self):
        faceted = utils.create_faceted_folder(self.portal, "Test Faceted")
        self.assertEqual("Test Faceted", faceted.title)
        self.assertEqual("test-faceted", faceted.id)
        IFacetedNavigable.providedBy(faceted)

    def test_create_faceted_folder_with_id(self):
        faceted = utils.create_faceted_folder(
            self.portal, "Test Faceted", id="test-faceted"
        )
        self.assertEqual("Test Faceted", faceted.title)
        self.assertEqual("test-faceted", faceted.id)
        IFacetedNavigable.providedBy(faceted)

    def test_set_constrain_types(self):
        constraints = ISelectableConstrainTypes(self.belleville)
        self.assertListEqual(["Meeting"], constraints.getLocallyAllowedTypes())
        utils.set_constrain_types(self.belleville, ["Meeting", "Folder"])
        self.assertListEqual(
            sorted(["Meeting", "Folder"]), sorted(constraints.getLocallyAllowedTypes())
        )
        utils.set_constrain_types(self.belleville, ["Meeting"])
        self.assertListEqual(["Meeting"], constraints.getLocallyAllowedTypes())

    def test_cleanup_contents(self):
        api.content.create(container=self.portal, id="news", type="Folder")
        self.assertTrue("news" in self.portal)
        utils.cleanup_contents()
        self.assertFalse("news" in self.portal)

    def test_get_global_category_no_mapping(self):
        institution = type("institution", (object,), {"categories_mappings": None})()
        self.assertEqual("foo", utils.get_global_category(institution, "foo"))

    def test_get_global_category_unknown_category(self):
        mapping = [{"local_category_id": "foo", "global_category_id": "bar"}]
        institution = type("institution", (object,), {"categories_mappings": mapping})()
        self.assertEqual("test", utils.get_global_category(institution, "test"))

    def test_get_global_category_mapping(self):
        mapping = [{"local_category_id": "foo", "global_category_id": "bar"}]
        institution = type("institution", (object,), {"categories_mappings": mapping})()
        self.assertEqual("bar", utils.get_global_category(institution, "foo"))

    def test_format_meeting_date_and_state(self):
        date = datetime(2019, 12, 31, 23, 59)
        # Base test
        formated_meeting_date = format_meeting_date_and_state(date, "private")
        self.assertEqual(formated_meeting_date, u"31 December 2019 (23:59) — private")
        # Test translation
        french_formated_meeting_date = format_meeting_date_and_state(
            date, "private", lang="fr"
        )
        self.assertEqual(
            french_formated_meeting_date, u"31 Décembre 2019 (23:59) — Privé"
        )
        french_formated_meeting_date = format_meeting_date_and_state(
            date, "in_project", lang="fr"
        )
        self.assertEqual(
            french_formated_meeting_date,
            u"31 Décembre 2019 (23:59) — Projet de décision",
        )
        french_formated_meeting_date = format_meeting_date_and_state(
            date, "decision", lang="fr"
        )
        self.assertEqual(
            french_formated_meeting_date, u"31 Décembre 2019 (23:59) — Décision"
        )
        # Test custom format
        french_custom_formated_meeting_date = format_meeting_date_and_state(
            date, "private", format="%A %d %B %Y", lang="fr"
        )
        self.assertEqual(
            french_custom_formated_meeting_date, u"Mardi 31 Décembre 2019 — Privé"
        )
