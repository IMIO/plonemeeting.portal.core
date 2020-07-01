# -*- coding: utf-8 -*-



from plonemeeting.portal.core.content.institution import validate_color_parameters
from plonemeeting.portal.core.content.institution import InvalidColorParameters
from plonemeeting.portal.core.tests.portal_test_case import (
    PmPortalDemoFunctionalTestCase,
)



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
