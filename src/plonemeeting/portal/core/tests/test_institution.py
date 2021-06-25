# -*- coding: utf-8 -*-

from AccessControl.PermissionRole import rolesForPermissionOn
from plone import api
from plone.app.theming.utils import compileThemeTransform
from plonemeeting.portal.core.content.institution import InvalidColorParameters
from plonemeeting.portal.core.content.institution import validate_color_parameters
from plonemeeting.portal.core.tests.portal_test_case import PmPortalDemoFunctionalTestCase
from Products.CMFCore.permissions import AccessContentsInformation as ACI
from Products.CMFPlone.interfaces import ISelectableConstrainTypes


class TestInstitutionView(PmPortalDemoFunctionalTestCase):
    def test_call_manager(self):
        institution = self.portal["belleville"]
        self.login_as_manager()
        view_content = institution.restrictedTraverse("@@view")()
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
