# -*- coding: utf-8 -*-

from AccessControl.PermissionRole import rolesForPermissionOn
from mockito import mock
from mockito import unstub
from mockito import verify
from mockito import when
from plone import api
from plone.app.theming.utils import compileThemeTransform
from plonemeeting.portal.core.content.institution import InvalidColorParameters
from plonemeeting.portal.core.content.institution import validate_color_parameters
from plonemeeting.portal.core.tests.portal_test_case import PmPortalDemoFunctionalTestCase
from Products.CMFCore.permissions import AccessContentsInformation
from Products.CMFPlone.interfaces import ISelectableConstrainTypes

import requests


class TestInstitutionView(PmPortalDemoFunctionalTestCase):

    def test_call_institution_view_as_manager(self):
        institution = self.portal["belleville"]
        self.login_as_admin()
        request = self.portal.REQUEST
        view = institution.restrictedTraverse("@@manage-settings")
        request.set("PUBLISHED", view)
        view_content = view()
        self.assertEqual(view.request.response.status, 200)
        self.assertTrue("Meeting config ID" in view_content)

    def test_call_institution_view_as_anonymous(self):
        institution = self.portal["belleville"]
        self.login_as_test()
        view = institution.restrictedTraverse("@@view")
        view_content = view()
        self.assertTrue("Meeting config ID" not in view_content)
        self.assertEqual(view.request.response.status, 302)
        self.assertDictEqual(view.request.response.headers, {"location": "http://nohost/plone/belleville/decisions"})

    def test_validate_color_parameters(self):
        self.assertTrue(validate_color_parameters("#FFF"))
        self.assertTrue(validate_color_parameters("#00ab44"))
        self.assertTrue(validate_color_parameters("#4200FF"))
        with self.assertRaises(InvalidColorParameters):
            validate_color_parameters("4200FF")
            validate_color_parameters("#XXXXXXXXX")

    def test_available_allowed_types(self):
        institution_constraints = ISelectableConstrainTypes(self.institution)
        decisions_constraints = ISelectableConstrainTypes(self.institution.decisions)
        publications_constraints = ISelectableConstrainTypes(self.institution.publications)
        self.login_as_admin()
        self.assertListEqual(["Folder"], institution_constraints.getLocallyAllowedTypes())
        self.assertListEqual(["Meeting"], decisions_constraints.getLocallyAllowedTypes())
        self.assertListEqual(["Publication"], publications_constraints.getLocallyAllowedTypes())
        self.login_as_test()
        self.assertListEqual([], institution_constraints.getLocallyAllowedTypes())
        self.assertListEqual([], decisions_constraints.getLocallyAllowedTypes())
        self.assertListEqual([], publications_constraints.getLocallyAllowedTypes())
        self.login_as_decisions_manager()
        self.assertListEqual([], institution_constraints.getLocallyAllowedTypes())
        # "Meeting" is not addable manually
        self.assertListEqual([], decisions_constraints.getLocallyAllowedTypes())
        self.assertListEqual([], publications_constraints.getLocallyAllowedTypes())
        self.login_as_publications_manager()
        self.assertListEqual([], institution_constraints.getLocallyAllowedTypes())
        self.assertListEqual([], decisions_constraints.getLocallyAllowedTypes())
        self.assertListEqual(["Publication"], publications_constraints.getLocallyAllowedTypes())

    def test_load_category_from_delib(self):
        belleville = self.portal["belleville"]
        json_categories = {
            "extra_include_categories": [
                {"id": "admin", "title": "Administrative"},
                {"id": "political", "title": "Political"},
            ]
        }
        json_classifiers = {
            "extra_include_classifiers": [
                {"id": "economy", "title": "Economy"},
                {"id": "env", "title": "Environment"},
            ]
        }

        json_rpz = {
            "extra_include_groups_in_charge": [
                {"UID": "", "title": ""},
            ]
        }

        url_cat = "https://demo-pm.imio.be/@config?config_id=meeting-config-college&extra_include=categories"
        auth = ("dgen", "meeting")
        headers = {"Content-type": "application/json", "Accept": "application/json"}

        when(requests).get(url_cat, auth=auth, headers=headers).thenReturn(
            mock({"status_code": 200, "json": lambda: json_categories})
        )

        url_rpz = "https://demo-pm.imio.be/@config?config_id=meeting-config-college&extra_include=groups_in_charge"
        when(requests).get(url_rpz, auth=auth, headers=headers).thenReturn(
            mock({"status_code": 200, "json": lambda: json_rpz})
        )

        tmp_var = belleville.plonemeeting_url
        belleville.plonemeeting_url = None
        belleville.fetch_delib_categories()
        self.assertDictEqual(belleville.delib_categories, {})

        belleville.plonemeeting_url = tmp_var
        tmp_var = belleville.meeting_config_id
        belleville.meeting_config_id = None
        belleville.fetch_delib_categories()
        self.assertDictEqual(belleville.delib_categories, {})

        belleville.meeting_config_id = tmp_var
        tmp_var = belleville.username
        belleville.username = None
        belleville.fetch_delib_categories()
        self.assertDictEqual(belleville.delib_categories, {})

        belleville.username = tmp_var
        tmp_var = belleville.password
        belleville.password = None
        belleville.fetch_delib_categories()
        self.assertDictEqual(belleville.delib_categories, {})

        belleville.password = tmp_var
        belleville.fetch_delib_categories()

        self.assertDictEqual({"admin": "Administrative", "political": "Political"}, belleville.delib_categories)
        verify(requests, times=1).get(url_cat, auth=auth, headers=headers)

        # edit the institution, only fetched one time
        self.login_as_admin()
        institution_edit_form = belleville.restrictedTraverse("@@edit")
        request = self.portal.REQUEST
        request.set("PUBLISHED", institution_edit_form)
        institution_edit_form()
        # was fetch a second time
        verify(requests, times=2).get(url_cat, auth=auth, headers=headers)
        # if any kind of data submitted, categories are no more fetched
        request.form["form.widgets.IBasic.title"] = "New Belleville title"
        institution_edit_form()
        verify(requests, times=2).get(url_cat, auth=auth, headers=headers)
        unstub()

        url = "https://demo-pm.imio.be/@config?config_id=meeting-config-college&extra_include=classifiers"
        when(requests).get(url, auth=auth, headers=headers).thenReturn(
            mock({"status_code": 200, "json": lambda: json_classifiers})
        )

        belleville.delib_category_field = "classifier"
        belleville.fetch_delib_categories()
        self.assertDictEqual({"economy": "Economy", "env": "Environment"}, belleville.delib_categories)
        unstub()
        # when requests.exceptions.ConnectionError is raised we gracefully fall back on last saved delib_categories
        when(requests).get(url, auth=auth, headers=headers).thenRaise(
            requests.exceptions.ConnectionError("mocked error")
        )
        setattr(belleville, "delib_categories", {"admin": "Administrative", "political": "Political"})
        belleville.fetch_delib_categories()
        self.assertDictEqual({"admin": "Administrative", "political": "Political"}, belleville.delib_categories)
        belleville.delib_categories = None
        belleville.fetch_delib_categories()
        self.assertDictEqual(belleville.delib_categories, {})

        delattr(belleville, "delib_categories")
        belleville.fetch_delib_categories()
        self.assertDictEqual(belleville.delib_categories, {})
        unstub()

    def test_load_representatives_from_delib(self):
        belleville = self.portal["belleville"]
        belleville.representatives_mappings = []
        json_categories = {
            "extra_include_categories": [
                {"id": "", "title": ""},
            ]
        }

        json_rpz = {
            "extra_include_groups_in_charge": [
                {"UID": "fake", "title": "Wolverine"},
                {"UID": "fake++", "title": "Cyclop"},
            ]
        }

        url_cat = "https://demo-pm.imio.be/@config?config_id=meeting-config-college&extra_include=categories"
        auth = ("dgen", "meeting")
        headers = {"Content-type": "application/json", "Accept": "application/json"}

        when(requests).get(url_cat, auth=auth, headers=headers).thenReturn(
            mock({"status_code": 200, "json": lambda: json_categories})
        )

        url_rpz = "https://demo-pm.imio.be/@config?config_id=meeting-config-college&extra_include=groups_in_charge"
        when(requests).get(url_rpz, auth=auth, headers=headers).thenReturn(
            mock({"status_code": 200, "json": lambda: json_rpz})
        )

        tmp_var = belleville.plonemeeting_url
        belleville.plonemeeting_url = None
        belleville.fetch_delib_representatives()
        self.assertFalse(hasattr("belleville", "delib_representatives"))

        belleville.plonemeeting_url = tmp_var
        tmp_var = belleville.meeting_config_id
        belleville.meeting_config_id = None
        belleville.fetch_delib_representatives()
        self.assertFalse(hasattr("belleville", "delib_representatives"))

        belleville.meeting_config_id = tmp_var
        tmp_var = belleville.username
        belleville.username = None
        belleville.fetch_delib_representatives()
        self.assertFalse(hasattr("belleville", "delib_representatives"))

        belleville.username = tmp_var
        tmp_var = belleville.password
        belleville.password = None
        belleville.fetch_delib_representatives()
        self.assertFalse(hasattr("belleville", "delib_representatives"))

        belleville.password = tmp_var
        belleville.fetch_delib_representatives()

        self.assertDictEqual({"fake": "Wolverine", "fake++": "Cyclop"}, belleville.delib_representatives)
        verify(requests, times=1).get(url_rpz, auth=auth, headers=headers)

        # edit the institution, only fetched one time
        self.login_as_admin()
        institution_edit_form = belleville.restrictedTraverse("@@edit")
        request = self.portal.REQUEST
        request.set("PUBLISHED", institution_edit_form)
        institution_edit_form()
        # was fetch a second time
        verify(requests, times=2).get(url_rpz, auth=auth, headers=headers)
        # if any kind of data submitted, categories are no more fetched
        request.form["form.widgets.IBasic.title"] = "New Belleville title"
        institution_edit_form()
        verify(requests, times=2).get(url_rpz, auth=auth, headers=headers)
        # ensure history is kept but not unused values
        belleville.delib_representatives = {"trololo": "Mr Trololo"}
        belleville.fetch_delib_representatives()
        self.assertDictEqual({"fake": "Wolverine", "fake++": "Cyclop"}, belleville.delib_representatives)
        belleville.representatives_mappings.append(
            {
                "representative_key": "trololo",
                "representative_value": "Mr Trololo",
                "representative_long_value": "Mr Trololo Bourgmestre F.F.",
                "active": True,
            }
        )
        belleville.delib_representatives = {"trololo": "Mr Trololo"}
        belleville.fetch_delib_representatives()
        self.assertDictEqual(
            {"trololo": "Unknown value: ${key}", "fake": "Wolverine", "fake++": "Cyclop"},
            belleville.delib_representatives,
        )

    def test_rules_xml_compilation(self):
        """Make sure the "/++theme++barceloneta/rules.xml" entity does compile.
        "Anonymous" must have the "AccessContentsInformation" permission
        so rules.xml is correctly compiled..."""
        rules = "/++theme++barceloneta/rules.xml"
        inst = self.institution
        self.layer["request"]["PUBLISHED"] = inst.decisions
        # when institution "published"
        self.assertEqual(api.content.get_state(inst), "published")
        self.assertTrue(compileThemeTransform(rules=rules))
        self.assertTrue("Anonymous" in rolesForPermissionOn(AccessContentsInformation, inst))
        self.login_as_admin()
        api.content.transition(inst, to_state="private")
        self.logout()
        # when institution "private"
        self.assertEqual(api.content.get_state(inst), "private")
        self.assertTrue(compileThemeTransform(rules=rules))
        self.assertTrue("Anonymous" in rolesForPermissionOn(AccessContentsInformation, inst))
