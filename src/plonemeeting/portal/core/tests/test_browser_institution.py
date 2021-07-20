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
        request = self.portal.REQUEST
        request.set('PUBLISHED', institution_view)
        institution_view.update()
        self.assertFalse(hasattr(self.belleville, "delib_categories"))

    def test_fetch_category_only_once_on_edit(self):
        self.login_as_manager()
        institution_edit_form = self.belleville.restrictedTraverse("@@edit")
        # context is overridden while traversing
        request = self.portal.REQUEST
        request.set('PUBLISHED', institution_edit_form)
        self.assertFalse(hasattr(self.belleville, "delib_categories"))
        institution_edit_form()
        self.assertListEqual([('travaux', 'Travaux'),
                              ('urbanisme', 'Urbanisme'),
                              ('comptabilite', 'Comptabilité'),
                              ('personnel', 'Personnel'),
                              ('population', 'Population / État-civil'),
                              ('locations', 'Locations'),
                              ('divers', 'Divers')],
                             self.belleville.delib_categories)

        delattr(self.belleville, "delib_categories")
        institution_edit_form.handleApply(institution_edit_form, None)
        self.assertFalse(hasattr(self.belleville, "delib_categories"))

        institution_edit_form.update()
        self.assertFalse(hasattr(self.belleville, "delib_categories"))

        institution_edit_form.render()
        self.assertFalse(hasattr(self.belleville, "delib_categories"))
