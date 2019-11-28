# -*- coding: utf-8 -*-

from Products.CMFPlone.interfaces.constrains import ISelectableConstrainTypes
from eea.facetednavigation.interfaces import IFacetedNavigable
from plone import api
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import login
from plone.app.testing import logout
from plone.app.testing import setRoles
from plonemeeting.portal.core.testing import (
    PLONEMEETING_PORTAL_DEMO_FUNCTIONAL_TESTING,
)  # noqa
from plonemeeting.portal.core import utils

import unittest


class TestUtils(unittest.TestCase):
    layer = PLONEMEETING_PORTAL_DEMO_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        login(self.portal, TEST_USER_NAME)
        self.belleville = self.portal["belleville"]

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
            "meeting-config-college&UID=foo&fullobjects=True",
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
            "https://demo-pm.imio.be/@search_meeting_items?getConfigId="
            "meeting-config-college&linkedMeetingUID=foo&fullobjects=True&review_state"
            "=itemfrozen&review_state=accepted&review_state=accepted_but_modified",
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
