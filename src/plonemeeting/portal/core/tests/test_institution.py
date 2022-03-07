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
from Products.CMFCore.permissions import AccessContentsInformation as ACI
from Products.CMFPlone.interfaces import ISelectableConstrainTypes

import requests


class TestInstitutionView(PmPortalDemoFunctionalTestCase):
    def test_call_institution_view_as_manager(self):
        institution = self.portal["belleville"]
        self.login_as_manager()
        request = self.portal.REQUEST
        view = institution.restrictedTraverse("@@view")
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
        self.assertDictEqual(
            view.request.response.headers,
            {"location": "http://nohost/plone/belleville/meetings"},
        )

    def test_validate_color_parameters(self):
        self.assertTrue(validate_color_parameters("#FFF"))
        self.assertTrue(validate_color_parameters("#00ab44"))
        self.assertTrue(validate_color_parameters("#4200FF"))
        with self.assertRaises(InvalidColorParameters):
            validate_color_parameters("4200FF")
            validate_color_parameters("#XXXXXXXXX")

    def test_available_allowed_types(self):
        constraints = ISelectableConstrainTypes(self.amityville)
        self.login_as_manager()
        self.assertListEqual(
            ["Folder", "Meeting"], constraints.getLocallyAllowedTypes()
        )
        self.login_as_test()
        self.assertListEqual([], constraints.getLocallyAllowedTypes())
        self.login_as_institution_manager()
        self.assertListEqual([], constraints.getLocallyAllowedTypes())

    def test_load_category_from_delib(self):
        json_categories = {
            "extra_include_categories": [
                {"id": "economy", "title": "Economy"},
                {"id": "env", "title": "Environment"},
            ]
        }

        json_classifiers = {
            "extra_include_classifiers": [
                {"id": "economy", "title": "Economy"},
                {"id": "env", "title": "Environment"},
            ]
        }

        url_cat = "http://localhost:20081/demo/@config?config_id=meeting-config-college&extra_include=categories"
        url_rpz = "http://localhost:20081/demo/@config?config_id=meeting-config-college&extra_include=classifiers"
        auth = ("dgen", "Meeting_12")
        headers = {"Content-type": "application/json", "Accept": "application/json"}

        tmp_var = self.belleville.plonemeeting_url
        self.belleville.plonemeeting_url = None
        self.belleville.fetch_delib_categories()
        self.assertDictEqual(self.belleville.delib_categories, {})

        self.belleville.plonemeeting_url = tmp_var
        tmp_var = self.belleville.meeting_config_id
        self.belleville.meeting_config_id = None
        self.belleville.fetch_delib_categories()
        self.assertDictEqual(self.belleville.delib_categories, {})

        self.belleville.meeting_config_id = tmp_var
        tmp_var = self.belleville.username
        self.belleville.username = None
        self.belleville.fetch_delib_categories()
        self.assertDictEqual(self.belleville.delib_categories, {})

        self.belleville.username = tmp_var
        tmp_var = self.belleville.password
        self.belleville.password = None
        self.belleville.fetch_delib_categories()
        self.assertDictEqual(self.belleville.delib_categories, {})

        self.belleville.password = tmp_var
        self.belleville.fetch_delib_categories()

        self.assertDictEqual(
            {
                "administration": "Administration générale",
                "animaux": "Bien-être animal",
                "batiments-communaux": "Bâtiments communaux",
                "communication": "Communication & Relations extérieures",
                "cultes": "Cultes",
                "culture": "Culture & Folklore",
                "divers": "Divers",
                "economie": "Développement économique & commercial",
                "enfance": "Petite enfance",
                "enseignement": "Enseignement",
                "environnement": "Propreté & Environnement",
                "espaces-publics": "Aménagement des espaces publics",
                "finances": "Finances",
                "immo": "Affaires immobilières",
                "informatique": "Informatique",
                "interculturalite": "Interculturalité & Égalité",
                "jeunesse": "Jeunesse",
                "logement": "Logement & Énergie",
                "mobilite": "Mobilité",
                "patrimoine": "Patrimoine",
                "police": "Zone de police",
                "politique": "Politique générale",
                "population": "État civil & Population",
                "quartier": "Participation relation avec les quartiers",
                "recurrents": "Récurrents",
                "sante": "Santé",
                "securite": "Sécurité & Prévention",
                "social": "Services sociaux",
                "sport": "Sport",
                "tourisme": "Tourisme",
                "urbanisme": "Urbanisme & Aménagement du territoire",
            },
            self.belleville.delib_categories,
        )

        # edit the institution, only fetched one time
        unstub()
        actual_representatives = requests.get('http://localhost:20081/demo/@config?'
                                              'config_id=meeting-config-college'
                                              '&extra_include=groups_in_charge',
                                              auth=auth,
                                              headers=headers)
        when(requests).get(url_cat, auth=auth, headers=headers).thenReturn(
            mock({"status_code": 200, "json": lambda: json_categories})
        )

        when(requests).get('http://localhost:20081/demo/@config?config_id=meeting-config-college'
                           '&extra_include=groups_in_charge',
                           auth=auth, headers=headers).thenReturn(actual_representatives)
        self.login_as_manager()
        institution_edit_form = self.belleville.restrictedTraverse("@@edit")
        request = self.portal.REQUEST
        request.set("PUBLISHED", institution_edit_form)
        institution_edit_form()
        # was fetch a second time
        verify(requests, times=1).get(url_cat, auth=auth, headers=headers)
        # if any kind of data submitted, categories are no more fetched
        request.form["form.widgets.IBasic.title"] = "New belleville title"
        institution_edit_form()
        verify(requests, times=1).get(url_cat, auth=auth, headers=headers)
        unstub()
        when(requests).get(url_rpz, auth=auth, headers=headers).thenReturn(
            mock({"status_code": 200, "json": lambda: json_classifiers})
        )
        self.belleville.delib_category_field = "classifier"
        self.belleville.fetch_delib_categories()
        self.assertDictEqual(
            {"economy": "Economy", "env": "Environment"},
            self.belleville.delib_categories,
        )
        # when requests.exceptions.ConnectionError is raised we gracefully fall back on last saved delib_categories
        when(requests).get(url_rpz, auth=auth, headers=headers).thenRaise(
            requests.exceptions.ConnectionError("mocked error")
        )
        setattr(
            self.belleville,
            "delib_categories",
            {"admin": "Administrative", "political": "Political"},
        )
        self.belleville.fetch_delib_categories()
        self.assertDictEqual(
            {"admin": "Administrative", "political": "Political"},
            self.belleville.delib_categories,
        )
        self.belleville.delib_categories = None
        self.belleville.fetch_delib_categories()
        self.assertDictEqual(self.belleville.delib_categories, {})

        delattr(self.belleville, "delib_categories")
        self.belleville.fetch_delib_categories()
        self.assertDictEqual(self.belleville.delib_categories, {})
        unstub()

    def test_load_representatives_from_delib(self):
        self.belleville.representatives_mappings = []
        json_categories = {"extra_include_categories": [{"id": "", "title": ""}, ]}

        json_rpz = {
            "extra_include_groups_in_charge": [
                {"UID": "fake", "title": "Wolverine"},
                {"UID": "fake++", "title": "Cyclop"},
            ]
        }

        url_cat = "http://localhost:20081/demo/@config?config_id=meeting-config-college&extra_include=categories"
        auth = (self.belleville.username, self.belleville.password)
        headers = {"Content-type": "application/json", "Accept": "application/json"}

        url_rpz = "http://localhost:20081/demo/@config?config_id=meeting-config-college&extra_include=groups_in_charge"

        tmp_var = self.belleville.plonemeeting_url
        self.belleville.plonemeeting_url = None
        self.belleville.fetch_delib_representatives()
        self.assertDictEqual(self.belleville.delib_representatives, {})

        self.belleville.plonemeeting_url = tmp_var
        tmp_var = self.belleville.meeting_config_id
        self.belleville.meeting_config_id = None
        self.belleville.fetch_delib_representatives()
        self.assertDictEqual(self.belleville.delib_representatives, {})

        self.belleville.meeting_config_id = tmp_var
        tmp_var = self.belleville.username
        self.belleville.username = None
        self.belleville.fetch_delib_representatives()
        self.assertDictEqual(self.belleville.delib_representatives, {})

        self.belleville.username = tmp_var
        tmp_var = self.belleville.password
        self.belleville.password = None
        self.belleville.fetch_delib_representatives()
        self.assertDictEqual(self.belleville.delib_representatives, {})

        self.belleville.password = tmp_var
        self.belleville.fetch_delib_representatives()
        self.assertListEqual(
            ["Bourgmestre", "Echevin du Personnel", "Echevin du Travaux"],
            list(self.belleville.delib_representatives.values()),
        )

        # edit the institution, only fetched one time
        when(requests).get(url_cat, auth=auth, headers=headers).thenReturn(
            mock({"status_code": 200, "json": lambda: json_categories})
        )

        when(requests).get(url_rpz, auth=auth, headers=headers).thenReturn(
            mock({"status_code": 200, "json": lambda: json_rpz})
        )

        self.login_as_manager()
        institution_edit_form = self.belleville.restrictedTraverse("@@edit")
        request = self.portal.REQUEST
        request.set("PUBLISHED", institution_edit_form)
        institution_edit_form()
        # was fetch a second time
        verify(requests, times=1).get(url_rpz, auth=auth, headers=headers)
        # if any kind of data submitted, categories are no more fetched
        request.form["form.widgets.IBasic.title"] = "New Belleville title"
        institution_edit_form()
        verify(requests, times=1).get(url_rpz, auth=auth, headers=headers)
        # ensure history is kept but not unused values
        self.belleville.delib_representatives = {"trololo": "Mr Trololo"}
        self.belleville.fetch_delib_representatives()
        self.assertDictEqual(
            {"fake": "Wolverine", "fake++": "Cyclop"},
            self.belleville.delib_representatives,
        )
        self.belleville.representatives_mappings.append(
            {
                "representative_key": "trololo",
                "representative_value": "Mr Trololo",
                "representative_long_value": "Mr Trololo Bourgmestre F.F.",
                "active": True,
            }
        )
        self.belleville.delib_representatives = {"trololo": "Mr Trololo"}
        self.belleville.fetch_delib_representatives()
        self.assertDictEqual(
            {
                "trololo": "Unknown value: ${key}",
                "fake": "Wolverine",
                "fake++": "Cyclop",
            },
            self.belleville.delib_representatives,
        )

    def test_rules_xml_compilation(self):
        """Make sure the "/++theme++barceloneta/rules.xml" entity does compile.
           "Anonymous" must have the "AccessContentsInformation" permission
           so rules.xml is correctly compiled..."""
        rules = "/++theme++barceloneta/rules.xml"
        inst = self.amityville
        self.layer["request"]["PUBLISHED"] = inst.meetings
        # when institution "published"
        self.assertEqual(api.content.get_state(inst), "published")
        self.assertTrue(compileThemeTransform(rules=rules))
        self.assertTrue("Anonymous" in rolesForPermissionOn(ACI, inst))
        self.login_as_manager()
        api.content.transition(inst, to_state="private")
        self.logout()
        # when institution "private"
        self.assertEqual(api.content.get_state(inst), "private")
        self.assertTrue(compileThemeTransform(rules=rules))
        self.assertTrue("Anonymous" in rolesForPermissionOn(ACI, inst))
