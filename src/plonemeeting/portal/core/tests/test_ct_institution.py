# -*- coding: utf-8 -*-
from Products.CMFPlone.interfaces import ISelectableConstrainTypes
from plone import api
from plone.api.content import get_state
from plone.api.exc import InvalidParameterError
from plone.api.portal import get_registry_record
from plone.dexterity.interfaces import IDexterityFTI
from plonemeeting.portal.core.config import APP_FOLDER_ID
from plonemeeting.portal.core.content.institution import IInstitution
from plonemeeting.portal.core.tests.portal_test_case import PmPortalTestCase
from plonemeeting.portal.core.utils import format_institution_managers_group_id
from zope.component import createObject
from zope.component import queryUtility
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent


class InstitutionIntegrationTest(PmPortalTestCase):
    def test_ct_institution_schema(self):
        fti = queryUtility(IDexterityFTI, name="Institution")
        schema = fti.lookupSchema()
        self.assertEqual(IInstitution, schema)

    def test_ct_institution_fti(self):
        fti = queryUtility(IDexterityFTI, name="Institution")
        self.assertTrue(fti)

    def test_ct_institution_factory(self):
        fti = queryUtility(IDexterityFTI, name="Institution")
        factory = fti.factory
        obj = createObject(factory)

        self.assertTrue(
            IInstitution.providedBy(obj),
            u"IInstitution not provided by {0}!".format(obj),
        )

    def test_ct_institution_adding(self):
        self.login_as_manager()
        obj = api.content.create(
            container=self.portal, type="Institution", id="institution"
        )

        group_id = format_institution_managers_group_id(obj)
        roles = api.group.get_roles(groupname=group_id)
        self.assertEqual(roles, ["Authenticated"])
        self.assertTupleEqual(
            obj.get_local_roles_for_userid(group_id),
            ("Institution Manager", "Contributor"),
        )

        self.assertTrue(
            IInstitution.providedBy(obj),
            u"IInstitution not provided by {0}!".format(obj.id),
        )

        faceted_folders = obj.listFolderContents()
        self.assertEqual(len(faceted_folders), 1)
        meetings = faceted_folders[0]
        constraints = ISelectableConstrainTypes(meetings)
        self.assertListEqual([], constraints.getLocallyAllowedTypes())

        agenda = api.content.create(obj, "Folder", "agenda")
        constraints = ISelectableConstrainTypes(agenda)
        self.assertListEqual(['Document', 'Folder', 'File', 'Image'],
                             constraints.getLocallyAllowedTypes())

        # check that deleting the object works too
        parent = obj.__parent__
        self.assertIn("institution", parent.objectIds())

        api.content.delete(obj=obj)
        self.assertNotIn("institution", parent.objectIds())
        self.assertIsNone(api.group.get(group_id))

    def test_ct_institution_globally_addable(self):
        self.login_as_manager()
        fti = queryUtility(IDexterityFTI, name="Institution")
        self.assertTrue(
            fti.global_allow, u"{0} is not globally addable!".format(fti.id)
        )

    def test_ct_institution_filter_content_type_true(self):
        self.login_as_manager()
        fti = queryUtility(IDexterityFTI, name="Institution")
        portal_types = self.portal.portal_types
        parent_id = portal_types.constructContent(
            fti.id, self.portal, "institution_id", title="Institution container"
        )
        parent = self.portal[parent_id]
        with self.assertRaises(InvalidParameterError):
            api.content.create(container=parent, type="Document", title="My Content")

    def test_ct_institution_transition_apply_to_children(self):
        institution = api.content.create(
            container=self.portal, type="Institution", id="test"
        )

        self.assertEqual(get_state(institution), 'private')
        meeting = api.content.create(
            container=institution, type="Meeting", id="test-meeting"
        )
        self.assertEqual(get_state(meeting), 'private')

        self.assertEqual(institution.listFolderContents({"portal_type": "Folder"}),
                         [institution.get(APP_FOLDER_ID)])
        meetings_folder = institution.listFolderContents()[0]
        self.assertEqual(get_state(meetings_folder), 'private')

        api.content.transition(institution, to_state='published')
        self.assertEqual(get_state(institution), 'published')
        self.assertEqual(get_state(meetings_folder), 'published')
        self.assertEqual(get_state(meeting), 'private')

        api.content.transition(institution, to_state='private')
        self.assertEqual(get_state(institution), 'private')
        self.assertEqual(get_state(meetings_folder), 'private')
        self.assertEqual(get_state(meeting), 'private')

        agenda_folder = api.content.create(type="Folder",
                                           title="Agenda",
                                           container=institution)
        # meeting are ignored when publishing the institution
        # but put back to private if the institution goes back in private
        api.content.transition(institution, to_state='published')
        self.assertEqual(get_state(institution), 'published')
        self.assertEqual(get_state(meetings_folder), 'published')
        self.assertEqual(get_state(agenda_folder), 'published')
        self.assertEqual(get_state(meeting), 'private')

        api.content.transition(meeting, to_state='decision')

        api.content.transition(institution, to_state='private')
        self.assertEqual(get_state(institution), 'private')
        self.assertEqual(get_state(meetings_folder), 'private')
        self.assertEqual(get_state(agenda_folder), 'private')
        self.assertEqual(get_state(meeting), 'private')

    def test_ct_institution_modified(self):
        self.login_as_manager()

        self.portal.portal_setup.runAllImportStepsFromProfile("profile-plonemeeting.portal.core:demo")
        institution = api.content.create(
            container=self.portal, type="Institution", id="institution"
        )
        self.assertFalse(hasattr(institution, "delib_categories"))
        self.assertIsNone(institution.categories_mappings)

        global_categories = get_registry_record(name="plonemeeting.portal.core.global_categories")
        institution.delib_categories = {}
        for cat_id in global_categories:
            institution.delib_categories[cat_id] = global_categories[cat_id]
        notify(ObjectModifiedEvent(institution))
        self.assertEqual(len(institution.categories_mappings), len(institution.delib_categories))
        self.assertListEqual(institution.categories_mappings,
                             [{"local_category_id": cat, "global_category_id": cat}
                              for cat in global_categories])
        # if categories_mappings is already initialized it is not overridden
        institution.delib_categories = {"administration": "Cat1", "animaux": "Cat2",
                                                 "cultes": "Cat3", "finances": "Cat4"}
        notify(ObjectModifiedEvent(institution))
        self.assertListEqual(institution.categories_mappings,
                             [{"local_category_id": cat, "global_category_id": cat}
                              for cat in global_categories])
        # now categories_mappings will be initialized with the new value
        institution.categories_mappings = []
        notify(ObjectModifiedEvent(institution))
        self.assertListEqual(institution.categories_mappings,
                             [{"local_category_id": "administration", "global_category_id": "administration"},
                              {"local_category_id": "animaux", "global_category_id": "animaux"},
                              {"local_category_id": "cultes", "global_category_id": "cultes"},
                              {"local_category_id": "finances", "global_category_id": "finances"}])
        # only matching ids are kept
        institution.delib_categories = {"massa": "quis", "vitae": "vel", "animaux": "Cat2",
                                        "tortor": "eros", "condimentum": "donec",
                                        "cultes": "Cat3", "lacinia": "ac"}
        institution.categories_mappings = []
        notify(ObjectModifiedEvent(institution))
        self.assertListEqual(institution.categories_mappings,
                             [{"local_category_id": "animaux", "global_category_id": "animaux"},
                              {"local_category_id": "cultes", "global_category_id": "cultes"}])
