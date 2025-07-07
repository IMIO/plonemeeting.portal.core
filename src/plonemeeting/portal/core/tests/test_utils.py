# -*- coding: utf-8 -*-
from datetime import datetime
from eea.facetednavigation.interfaces import IFacetedNavigable
from plone import api
from plonemeeting.portal.core import utils
from plonemeeting.portal.core.tests.portal_test_case import PmPortalDemoFunctionalTestCase
from plonemeeting.portal.core.utils import format_meeting_date_and_state
from Products.CMFPlone.interfaces.constrains import ISelectableConstrainTypes


class TestUtils(PmPortalDemoFunctionalTestCase):
    def setUp(self):
        super().setUp()
        self.belleville = self.portal["belleville"]
        self.login_as_admin()

    def tearDown(self):
        if "test-faceted" in self.portal:
            api.content.delete(self.portal["test-faceted"])
        super(TestUtils, self).tearDown()

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
        url = utils.get_api_url_for_meetings(self.belleville, meeting_external_uid="foo")
        self.assertEqual(
            "https://demo-pm.imio.be/@search?"
            "type=meeting"
            "&config_id=meeting-config-college"
            "&UID=foo"
            "&fullobjects=True"
            "&include_all=false"
            "&metadata_fields=date"
            "&b_size=9999",
            url,
        )

    def test_get_api_url_for_meetings_additional_query(self):
        url = utils.get_api_url_for_meetings(self.belleville)
        self.assertEqual(
            "https://demo-pm.imio.be/@search?"
            "type=meeting"
            "&config_id=meeting-config-college"
            "&review_state=frozen",
            url,
        )

    def test_get_api_url_for_annexes(self):
        url = utils.get_api_url_for_annexes(
            "https://demo-pm.imio.be/foo")
        self.assertEqual(
            "https://demo-pm.imio.be/foo/@annexes?"
            "publishable=true"
            "&fullobjects"
            "&include_all=false"
            "&metadata_fields=file"
            "&metadata_fields=content_category"
            "&additional_values=publishable"
            "&additional_values=category_title"
            "&additional_values=subcategory_title",
            url,
        )

    def test_get_api_url_for_meeting_items(self):
        # test empty category_mappings
        self.belleville.categories_mappings = None
        url = utils.get_api_url_for_meeting_items(self.belleville, "foo")
        self.assertEqual(
            "https://demo-pm.imio.be/@search?"
            "type=item"
            "&sort_on=getItemNumber"
            "&privacy=public"
            "&privacy=public_heading"
            "&b_size=9999"
            "&additional_values=formatted_itemNumber"
            "&config_id=meeting-config-college"
            "&linkedMeetingUID=foo"
            "&meeting_uid=foo"
            "&fullobjects=True"
            "&include_all=false"
            "&metadata_fields=itemNumber"
            "&metadata_fields=groupsInCharge"
            "&metadata_fields=category"
            "&review_state=itemfrozen"
            "&review_state=accepted"
            "&review_state=accepted_but_modified"
            "&getCategory=VOID"
            "&getGroupsInCharge=7a82fee367a0416f8d7e8f4a382db0d1"
            "&getGroupsInCharge=a2396143f11f4e2292f12ee3b3447739"
            "&getGroupsInCharge=bf5fccd9bc9048e9957680c7ab5576b4"
            "&getGroupsInCharge=f3f9e7808ddb4e56946b2dba6370eb9b"
            "&extra_include=public_deliberation",
            url,
        )
        self.belleville.delib_category_field = "classifier"
        url = utils.get_api_url_for_meeting_items(self.belleville, "foo")
        self.assertEqual(
            "https://demo-pm.imio.be/@search?"
            "type=item"
            "&sort_on=getItemNumber"
            "&privacy=public"
            "&privacy=public_heading"
            "&b_size=9999"
            "&additional_values=formatted_itemNumber"
            "&config_id=meeting-config-college"
            "&linkedMeetingUID=foo"
            "&meeting_uid=foo"
            "&fullobjects=True"
            "&include_all=false"
            "&metadata_fields=itemNumber"
            "&metadata_fields=groupsInCharge"
            "&metadata_fields=classifier"
            "&review_state=itemfrozen"
            "&review_state=accepted"
            "&review_state=accepted_but_modified"
            "&getRawClassifier=VOID"
            "&getGroupsInCharge=7a82fee367a0416f8d7e8f4a382db0d1"
            "&getGroupsInCharge=a2396143f11f4e2292f12ee3b3447739"
            "&getGroupsInCharge=bf5fccd9bc9048e9957680c7ab5576b4"
            "&getGroupsInCharge=f3f9e7808ddb4e56946b2dba6370eb9b"
            "&extra_include=public_deliberation",
            url,
        )
        self.belleville.categories_mappings = [{'local_category_id': 'administration',
                                                'global_category_id': 'administration'},
                                               {'local_category_id': 'immo',
                                                'global_category_id': 'immo'}]
        url = utils.get_api_url_for_meeting_items(self.belleville, "foo")
        self.assertEqual(
            "https://demo-pm.imio.be/@search?"
            "type=item"
            "&sort_on=getItemNumber"
            "&privacy=public"
            "&privacy=public_heading"
            "&b_size=9999"
            "&additional_values=formatted_itemNumber"
            "&config_id=meeting-config-college"
            "&linkedMeetingUID=foo"
            "&meeting_uid=foo"
            "&fullobjects=True"
            "&include_all=false"
            "&metadata_fields=itemNumber"
            "&metadata_fields=groupsInCharge"
            "&metadata_fields=classifier"
            "&review_state=itemfrozen"
            "&review_state=accepted"
            "&review_state=accepted_but_modified"
            "&getRawClassifier=administration"
            "&getRawClassifier=immo"
            "&getGroupsInCharge=7a82fee367a0416f8d7e8f4a382db0d1"
            "&getGroupsInCharge=a2396143f11f4e2292f12ee3b3447739"
            "&getGroupsInCharge=bf5fccd9bc9048e9957680c7ab5576b4"
            "&getGroupsInCharge=f3f9e7808ddb4e56946b2dba6370eb9b"
            "&extra_include=public_deliberation",
            url,
        )
        self.belleville.delib_category_field = "category"
        url = utils.get_api_url_for_meeting_items(self.belleville, "foo")
        self.assertEqual(
            "https://demo-pm.imio.be/@search?"
            "type=item"
            "&sort_on=getItemNumber"
            "&privacy=public"
            "&privacy=public_heading"
            "&b_size=9999"
            "&additional_values=formatted_itemNumber"
            "&config_id=meeting-config-college"
            "&linkedMeetingUID=foo"
            "&meeting_uid=foo"
            "&fullobjects=True"
            "&include_all=false"
            "&metadata_fields=itemNumber"
            "&metadata_fields=groupsInCharge"
            "&metadata_fields=category"
            "&review_state=itemfrozen"
            "&review_state=accepted"
            "&review_state=accepted_but_modified"
            "&getCategory=administration"
            "&getCategory=immo"
            "&getGroupsInCharge=7a82fee367a0416f8d7e8f4a382db0d1"
            "&getGroupsInCharge=a2396143f11f4e2292f12ee3b3447739"
            "&getGroupsInCharge=bf5fccd9bc9048e9957680c7ab5576b4"
            "&getGroupsInCharge=f3f9e7808ddb4e56946b2dba6370eb9b"
            "&extra_include=public_deliberation",
            url,
        )

        self.belleville.representatives_mappings = None
        url = utils.get_api_url_for_meeting_items(self.belleville, "foo")
        self.assertEqual(
            "https://demo-pm.imio.be/@search?"
            "type=item"
            "&sort_on=getItemNumber"
            "&privacy=public"
            "&privacy=public_heading"
            "&b_size=9999"
            "&additional_values=formatted_itemNumber"
            "&config_id=meeting-config-college"
            "&linkedMeetingUID=foo"
            "&meeting_uid=foo"
            "&fullobjects=True"
            "&include_all=false"
            "&metadata_fields=itemNumber"
            "&metadata_fields=groupsInCharge"
            "&metadata_fields=category"
            "&review_state=itemfrozen"
            "&review_state=accepted"
            "&review_state=accepted_but_modified"
            "&getCategory=administration"
            "&getCategory=immo"
            "&extra_include=public_deliberation",
            url,
        )
        self.belleville.categories_mappings = None
        url = utils.get_api_url_for_meeting_items(self.belleville, "foo")
        self.assertEqual(
            "https://demo-pm.imio.be/@search?"
            "type=item"
            "&sort_on=getItemNumber"
            "&privacy=public"
            "&privacy=public_heading"
            "&b_size=9999"
            "&additional_values=formatted_itemNumber"
            "&config_id=meeting-config-college"
            "&linkedMeetingUID=foo"
            "&meeting_uid=foo"
            "&fullobjects=True"
            "&include_all=false"
            "&metadata_fields=itemNumber"
            "&metadata_fields=groupsInCharge"
            "&metadata_fields=category"
            "&review_state=itemfrozen"
            "&review_state=accepted"
            "&review_state=accepted_but_modified"
            "&getCategory=VOID"
            "&extra_include=public_deliberation",
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
        faceted = utils.create_faceted_folder(
            self.portal, "Test Faceted", id="test-faceted")
        self.assertEqual("Test Faceted", faceted.title)
        self.assertEqual("test-faceted", faceted.id)
        IFacetedNavigable.providedBy(faceted)

    def test_set_constrain_types(self):
        constraints = ISelectableConstrainTypes(self.belleville)
        self.assertListEqual(
            sorted(["Folder"]), sorted(constraints.getLocallyAllowedTypes())
        )
        utils.set_constrain_types(self.belleville, [])
        self.assertListEqual([], constraints.getLocallyAllowedTypes())
        utils.set_constrain_types(self.belleville, ["Folder"])
        self.assertListEqual(["Folder"], constraints.getLocallyAllowedTypes())

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

    def test_get_api_url_for_categories(self):
        url = utils.get_api_url_for_categories(self.belleville, "foo")
        self.assertEqual(
            "https://demo-pm.imio.be/@config?config_id=meeting-config-college&extra_include=foo",
            url,
        )
        self.belleville.plonemeeting_url = None
        self.assertIsNone(utils.get_api_url_for_categories(self.belleville, "foo"))

        self.belleville.plonemeeting_url = "https://demo-pm.imio.be"
        self.belleville.meeting_config_id = None
        self.assertIsNone(utils.get_api_url_for_categories(self.belleville, "foo"))

    def test_get_term_title(self):
        self.assertEqual(utils.get_term_title(self.belleville, "meeting_type"), "Séance publique du Conseil")
        self.assertEqual(utils.get_term_title(self.belleville, "institution_type"), "Ville/Commune")
        self.assertRaises(ValueError, utils.get_term_title, self.belleville, "no_such_field")
        self.assertRaises(ValueError, utils.get_term_title, self.belleville, "plonemeeting_url")
