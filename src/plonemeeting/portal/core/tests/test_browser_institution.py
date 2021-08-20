# -*- coding: utf-8 -*-
from copy import deepcopy
from plonemeeting.portal.core.content.institution import IInstitution
from plonemeeting.portal.core.tests.portal_test_case import PmPortalDemoFunctionalTestCase
from z3c.form import validator


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

    def test_categories_mappings_invariant(self):
        data = {'categories_mappings': deepcopy(self.belleville.categories_mappings)}
        invariants = validator.InvariantsValidator(None, None, None, IInstitution, None)
        self.login_as_manager()
        institution_edit_form = self.belleville.restrictedTraverse("@@edit")
        # context is overridden while traversing
        request = self.portal.REQUEST
        request.set('PUBLISHED', institution_edit_form)
        self.assertTupleEqual((), invariants.validate(data))
        data['categories_mappings'].append({'global_category_id': 'administration',
                                            'local_category_id': 'administration'})
        validation = invariants.validate(data)
        self.assertEqual(1, len(validation))
        self.assertEqual(str(validation[0]), 'iA.Delib category mapped more than once: Administration générale')
        data['categories_mappings'].append({'global_category_id': 'police',
                                            'local_category_id': 'police'})
        validation = invariants.validate(data)
        self.assertEqual(1, len(validation))
        self.assertEqual(str(validation[0]), 'iA.Delib category mapped more than once: '
                                             'Administration générale, Zone de police')
        # multiple time the same value returns only once in the message
        data['categories_mappings'].append({'global_category_id': 'administration',
                                            'local_category_id': 'administration'})
        validation = invariants.validate(data)
        self.assertEqual(1, len(validation))
        self.assertEqual(str(validation[0]), 'iA.Delib category mapped more than once: '
                                             'Administration générale, Zone de police')
