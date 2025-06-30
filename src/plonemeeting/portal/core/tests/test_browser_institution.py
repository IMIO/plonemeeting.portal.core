# -*- coding: utf-8 -*-
from copy import deepcopy
from plonemeeting.portal.core.content.institution import IInstitution
from plonemeeting.portal.core.content.institution import representatives_mappings_invariant
from plonemeeting.portal.core.tests.portal_test_case import PmPortalDemoFunctionalTestCase
from z3c.form import validator
from zope.i18n import translate
from zope.interface import Invalid


class TestBrowserInstitution(PmPortalDemoFunctionalTestCase):
    @property
    def belleville(self):
        return self.portal["belleville"]

    @property
    def amityville(self):
        return self.portal["amityville"]

    def exc_msg(self, invalid):
        return translate(invalid.args[0], context=self.portal.REQUEST)

    def test_not_fetch_category_on_view(self):
        self.login_as_admin()
        institution_view = self.belleville.restrictedTraverse("@@view")
        # context is overridden while traversing
        self.assertFalse(hasattr(self.belleville, "delib_categories"))
        request = self.portal.REQUEST
        request.set('PUBLISHED', institution_view)
        institution_view.update()
        self.assertFalse(hasattr(self.belleville, "delib_categories"))

    def test_fetch_category_only_once_on_edit(self):
        self.login_as_admin()
        institution_edit_form = self.belleville.restrictedTraverse("@@edit")
        # context is overridden while traversing
        request = self.portal.REQUEST
        request.set('PUBLISHED', institution_edit_form)
        self.assertFalse(hasattr(self.belleville, "delib_categories"))
        institution_edit_form()
        self.assertDictEqual({'travaux': 'Travaux',
                              'urbanisme': 'Urbanisme',
                              'comptabilite': 'Comptabilité',
                              'personnel': 'Personnel',
                              'population': 'Population / État-civil',
                              'locations': 'Locations',
                              'divers': 'Divers',
                              'engagement': 'Engagement',
                              'finances': 'Finances'},
                             self.belleville.delib_categories)

        delattr(self.belleville, "delib_categories")
        institution_edit_form.handleApply(institution_edit_form, None)
        self.assertFalse(hasattr(self.belleville, "delib_categories"))

        institution_edit_form.update()
        self.assertFalse(hasattr(self.belleville, "delib_categories"))

        institution_edit_form.render()
        self.assertFalse(hasattr(self.belleville, "delib_categories"))

    def test_categories_mappings_invariant(self):
        data = {'categories_mappings': deepcopy(self.amityville.categories_mappings)}
        invariants = validator.InvariantsValidator(None, None, None, IInstitution, None)
        self.assertTupleEqual((), invariants.validate(data))
        data['categories_mappings'].append({'global_category_id': 'administration',
                                            'local_category_id': 'administration'})
        validation = invariants.validate(data)
        self.assertEqual(1, len(validation))
        self.assertEqual(
            translate(self.exc_msg(validation[0])),
            'Categories mappings - iA.Delib category mapped more than once : '
            'Administration générale')
        data['categories_mappings'].append({'global_category_id': 'police',
                                            'local_category_id': 'police'})
        validation = invariants.validate(data)
        self.assertEqual(1, len(validation))
        self.assertEqual(
            translate(self.exc_msg(validation[0])),
            'Categories mappings - iA.Delib category mapped more than once : '
            'Administration générale, Zone de police')
        # multiple time the same value returns only once in the message
        data['categories_mappings'].append(
            {'global_category_id': 'administration',
             'local_category_id': 'administration'})
        validation = invariants.validate(data)
        self.assertEqual(1, len(validation))
        self.assertEqual(
            translate(self.exc_msg(validation[0])),
            'Categories mappings - iA.Delib category mapped more than once : '
            'Administration générale, Zone de police')

    def test_representatives_mappings_invariant(self):
        class Mock(dict):
            def __init__(self, institution, categories_mappings, representatives_mappings):
                self.__context__ = institution
                self.categories_mappings = deepcopy(categories_mappings)
                self.representatives_mappings = deepcopy(representatives_mappings)
        data = Mock(
            None,
            self.belleville.categories_mappings,
            self.belleville.representatives_mappings)
        representatives_mappings_invariant(data)
        data = Mock(
            self.belleville,
            self.belleville.categories_mappings,
            self.belleville.representatives_mappings)
        representatives_mappings_invariant(data)
        data.representatives_mappings[0]['active'] = False
        data.representatives_mappings[0]['representative_long_value'] = 'fake name long'
        data.representatives_mappings[0]['representative_value'] = 'fake name'
        representatives_mappings_invariant(data)
        uid = data.representatives_mappings[0]['representative_key']
        data.representatives_mappings[0]['representative_key'] = 'fake uid'
        self.assertRaises(Invalid, representatives_mappings_invariant, data)
        try:
            representatives_mappings_invariant(data)
        except Invalid as error:
            self.assertEqual(translate(self.exc_msg(error)),
                             'Representatives mappings - Removing representatives '
                             'linked to items is not allowed : Mme LOREM')
        data.representatives_mappings[0]['representative_key'] = uid
        representatives_mappings_invariant(data)
        data.representatives_mappings.append({'active': True,
                                              'representative_key': 'fake uid',
                                              'representative_long_value': 'fake name long',
                                              'representative_value': 'fake name'}, )
        representatives_mappings_invariant(data)

        data.__context__.representatives_mappings = None # Could be None in Plone 6
        representatives_mappings_invariant(data)
