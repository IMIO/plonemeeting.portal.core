# -*- coding: utf-8 -*-

from AccessControl.PermissionRole import rolesForPermissionOn
from plone import api
from plone.app.theming.utils import compileThemeTransform
from Products.CMFCore.permissions import AccessContentsInformation as ACI
from Products.CMFPlone.interfaces import ISelectableConstrainTypes
from plonemeeting.portal.core.content.institution import validate_color_parameters
from plonemeeting.portal.core.content.institution import InvalidColorParameters
from plonemeeting.portal.core.tests.portal_test_case import (
    PmPortalDemoFunctionalTestCase,
)
from mockito import when, mock, verify, unstub
import requests


class TestInstitutionView(PmPortalDemoFunctionalTestCase):
    def test_call_manager(self):
        institution = self.portal["belleville"]
        self.login_as_manager()
        request = self.portal.REQUEST
        view = institution.restrictedTraverse("@@view")
        request.set('PUBLISHED', view)
        view_content = view()
        self.assertTrue("Meeting config ID" in view_content)

    def test_call_anonymous(self):
        institution = self.portal["belleville"]
        self.login_as_test()
        view_content = institution.restrictedTraverse("@@view")()
        self.assertTrue("Meeting config ID" not in view_content)

    def test_validate_color_parameters(self):
        self.assertTrue(validate_color_parameters("#FFF"))
        self.assertTrue(validate_color_parameters("#00ab44"))
        self.assertTrue(validate_color_parameters("#4200FF"))
        with self.assertRaises(InvalidColorParameters):
            validate_color_parameters("4200FF")
            validate_color_parameters("#XXXXXXXXX")

    def test_available_allowed_types(self):
        constraints = ISelectableConstrainTypes(self.institution)
        self.login_as_manager()
        self.assertListEqual(["Folder", "Meeting"], constraints.getLocallyAllowedTypes())
        self.login_as_test()
        self.assertListEqual([], constraints.getLocallyAllowedTypes())
        self.login_as_institution_manager()
        self.assertListEqual([], constraints.getLocallyAllowedTypes())

    def test_load_category_from_delib(self):
        belleville = self.portal["belleville"]
        json_categories = {"extra_include_categories": [
            {"id": "admin", "title": "Administrative"},
            {"id": "political", "title": "Political"},
        ]}
        json_classifiers = {"extra_include_classifiers": [
            {"id": "economy", "title": "Economy"},
            {"id": "env", "title": "Environment"},
        ]}

        url = 'https://demo-pm.imio.be/@config?config_id=meeting-config-college&extra_include=categories'
        auth = ('dgen', 'meeting')
        headers = {'Content-type': 'application/json', 'Accept': 'application/json'}

        when(requests).get(url, auth=auth, headers=headers)\
            .thenReturn(mock({'status_code': 200, 'json': lambda: json_categories}))

        tmp_var = belleville.plonemeeting_url
        belleville.plonemeeting_url = None
        belleville.fetch_delib_categories()
        self.assertFalse(hasattr(belleville, "delib_categories"))

        belleville.plonemeeting_url = tmp_var
        tmp_var = belleville.meeting_config_id
        belleville.meeting_config_id = None
        belleville.fetch_delib_categories()
        self.assertFalse(hasattr(belleville, "delib_categories"))

        belleville.meeting_config_id = tmp_var
        tmp_var = belleville.username
        belleville.username = None
        belleville.fetch_delib_categories()
        self.assertFalse(hasattr(belleville, "delib_categories"))

        belleville.username = tmp_var
        tmp_var = belleville.password
        belleville.password = None
        belleville.fetch_delib_categories()
        self.assertFalse(hasattr(belleville, "delib_categories"))

        belleville.password = tmp_var
        belleville.fetch_delib_categories()

        self.assertListEqual([('admin', 'Administrative'),
                              ('political', 'Political')],
                             belleville.delib_categories)
        verify(requests, times=1).get(url, auth=auth, headers=headers)

        # edit the institution, only fetched one time
        self.login_as_manager()
        institution_edit_form = belleville.restrictedTraverse("@@edit")
        request = self.portal.REQUEST
        request.set('PUBLISHED', institution_edit_form)
        institution_edit_form()
        # was fetch a second time
        verify(requests, times=2).get(url, auth=auth, headers=headers)
        # if any kind of data submitted, categories are no more fetched
        request.form["form.widgets.IBasic.title"] = "New Belleville title"
        institution_edit_form()
        verify(requests, times=2).get(url, auth=auth, headers=headers)
        # submit

        unstub()

        url = 'https://demo-pm.imio.be/@config?config_id=meeting-config-college&extra_include=classifiers'

        when(requests).get(url, auth=auth, headers=headers).thenReturn(
            mock({'status_code': 200, 'json': lambda: json_classifiers}))

        belleville.delib_category_field = "classifier"

        belleville.fetch_delib_categories()
        self.assertListEqual([('economy', 'Economy'),
                              ('env', 'Environment')],
                             belleville.delib_categories)
        unstub()

    def test_rules_xml_compilation(self):
        """Make sure the "/++theme++barceloneta/rules.xml" entity does compile.
           "Anonymous" must have the "AccessContentsInformation" permission
           so rules.xml is correctly compiled..."""
        rules = "/++theme++barceloneta/rules.xml"
        inst = self.institution
        self.layer['request']['PUBLISHED'] = inst.meetings
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
