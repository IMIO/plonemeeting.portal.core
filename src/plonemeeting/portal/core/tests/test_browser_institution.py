# -*- coding: utf-8 -*-
from plonemeeting.portal.core.tests.portal_test_case import (
    PmPortalDemoFunctionalTestCase,
)


class TestBrowserInstitution(PmPortalDemoFunctionalTestCase):
    @property
    def belleville(self):
        return self.portal["belleville"]

    def test_not_fetch_category_on_view(self):
        self.login_as_manager()
        institution_view = self.belleville.restrictedTraverse("@@view")
        # context is overridden while traversing
        self.assertFalse(hasattr(self.belleville, "delib_categories"))
        institution_view.update()
        self.assertFalse(hasattr(self.belleville, "delib_categories"))
