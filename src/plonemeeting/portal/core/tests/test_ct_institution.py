# -*- coding: utf-8 -*-
from plone import api
from plone.api.content import get_state
from plone.api.exc import InvalidParameterError
from plone.api.portal import get_registry_record
from plone.dexterity.interfaces import IDexterityFTI
from plonemeeting.portal.core.config import DEC_FOLDER_ID
from plonemeeting.portal.core.config import PUB_FOLDER_ID
from plonemeeting.portal.core.content.institution import IInstitution
from plonemeeting.portal.core.tests.portal_test_case import PmPortalTestCase
from plonemeeting.portal.core.utils import get_decisions_managers_group_id
from plonemeeting.portal.core.utils import get_publications_managers_group_id
from Products.CMFPlone.interfaces import ISelectableConstrainTypes
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
            "IInstitution not provided by {0}!".format(obj),
        )

    def test_ct_institution_adding(self):
        self.login_as_admin()
        institution = api.content.create(container=self.portal, type="Institution", id="institution")
        self.assertTrue(
            IInstitution.providedBy(institution),
            "IInstitution not provided by {0}!".format(institution.id),
        )

        for group_id in (get_decisions_managers_group_id(institution), get_publications_managers_group_id(institution)):
            roles = api.group.get_roles(groupname=group_id)
            self.assertEqual(roles, ["Authenticated"])
            self.assertTupleEqual(
                institution.get_local_roles_for_userid(group_id),
                ("Reader",),
            )

        institution_folders = institution.listFolderContents()
        self.assertEqual(len(institution_folders), 3)
        meetings = institution_folders[0]
        self.assertEqual(meetings.getId(), DEC_FOLDER_ID)
        constraints = ISelectableConstrainTypes(meetings)
        self.assertListEqual(["Meeting"], constraints.getLocallyAllowedTypes())

        publications = institution_folders[1]
        self.assertEqual(publications.getId(), PUB_FOLDER_ID)
        constraints = ISelectableConstrainTypes(publications)
        self.assertListEqual(["Publication"], constraints.getLocallyAllowedTypes())

        templates = institution_folders[2]
        self.assertEqual(templates.getId(), "templates")
        constraints = ISelectableConstrainTypes(templates)
        self.assertListEqual(
            ["PODTemplate", "ConfigurablePODTemplate", "StyleTemplate", "SubTemplate"],
            constraints.getLocallyAllowedTypes(),
        )

        agenda = api.content.create(institution, "Folder", "agenda")
        constraints = ISelectableConstrainTypes(agenda)
        self.assertSetEqual(
            {
                "Document",
                "Folder",
                "File",
                "Image",
                "Meeting",
                "Publication",
                "PODTemplate",
                "ConfigurablePODTemplate",
                "StyleTemplate",
                "SubTemplate",
            },
            set(constraints.getLocallyAllowedTypes()),
        )

        # check that deleting the object works too
        parent = institution.__parent__
        self.assertIn("institution", parent.objectIds())

        api.content.delete(obj=institution)
        self.assertNotIn("institution", parent.objectIds())
        self.assertIsNone(api.group.get(group_id))

    def test_ct_institution_globally_addable(self):
        self.login_as_admin()
        fti = queryUtility(IDexterityFTI, name="Institution")
        self.assertTrue(fti.global_allow, "{0} is not globally addable!".format(fti.id))

    def test_ct_institution_filter_content_type_true(self):
        self.login_as_admin()
        fti = queryUtility(IDexterityFTI, name="Institution")
        portal_types = self.portal.portal_types
        parent_id = portal_types.constructContent(fti.id, self.portal, "institution_id", title="Institution container")
        parent = self.portal[parent_id]
        with self.assertRaises(InvalidParameterError):
            api.content.create(container=parent, type="Document", title="My Content")

    def test_ct_institution_transition_apply_to_children(self):
        institution = api.content.create(container=self.portal, type="Institution", id="test")

        self.assertEqual(get_state(institution), "private")
        decisions = institution.decisions
        meeting = api.content.create(container=decisions, type="Meeting", id="test-meeting")
        self.assertEqual(get_state(meeting), "private")

        self.assertEqual(
            institution.listFolderContents({"portal_type": "Folder"}),
            [institution[DEC_FOLDER_ID], institution[PUB_FOLDER_ID], institution["templates"]],
        )
        decisions_folder = institution.decisions
        publications_folder = institution.publications
        self.assertEqual(get_state(decisions_folder), "private")
        self.assertEqual(get_state(publications_folder), "private")
        self.assertEqual(institution.enabled_tabs, [DEC_FOLDER_ID, PUB_FOLDER_ID])

        api.content.transition(institution, to_state="published")
        self.assertEqual(get_state(institution), "published")
        self.assertEqual(get_state(decisions_folder), "published")
        self.assertEqual(get_state(meeting), "private")
        self.assertEqual(get_state(publications_folder), "published")

        api.content.transition(institution, to_state="private")
        self.assertEqual(get_state(institution), "private")
        self.assertEqual(get_state(decisions_folder), "private")
        self.assertEqual(get_state(meeting), "private")
        self.assertEqual(get_state(publications_folder), "private")

        agenda_folder = api.content.create(type="Folder", title="Agenda", container=institution)
        # meeting are ignored when publishing the institution
        # but put back to private if the institution goes back in private
        api.content.transition(institution, to_state="published")
        self.assertEqual(get_state(institution), "published")
        self.assertEqual(get_state(decisions_folder), "published")
        self.assertEqual(get_state(agenda_folder), "published")
        self.assertEqual(get_state(meeting), "private")
        self.assertEqual(get_state(publications_folder), "published")

        api.content.transition(meeting, to_state="decision")
        api.content.transition(institution, to_state="private")
        self.assertEqual(get_state(institution), "private")
        self.assertEqual(get_state(decisions_folder), "private")
        self.assertEqual(get_state(agenda_folder), "private")
        self.assertEqual(get_state(meeting), "private")

    def test_ct_institution_modified(self):
        self.login_as_admin()

        self.portal.portal_setup.runAllImportStepsFromProfile("profile-plonemeeting.portal.core:demo")
        institution = api.content.create(container=self.portal, type="Institution", id="institution")
        self.assertFalse(hasattr(institution, "delib_categories"))
        self.assertIsNone(institution.categories_mappings)

        global_categories = get_registry_record(name="plonemeeting.portal.core.global_categories")
        institution.delib_categories = {}
        for cat_id in global_categories:
            institution.delib_categories[cat_id] = global_categories[cat_id]
        notify(ObjectModifiedEvent(institution))
        self.assertEqual(len(institution.categories_mappings), len(institution.delib_categories))
        self.assertListEqual(
            institution.categories_mappings,
            [{"local_category_id": cat, "global_category_id": cat} for cat in global_categories],
        )
        # if categories_mappings is already initialized it is not overridden
        institution.delib_categories = {
            "administration": "Cat1",
            "animaux": "Cat2",
            "cultes": "Cat3",
            "finances": "Cat4",
        }
        notify(ObjectModifiedEvent(institution))
        self.assertListEqual(
            institution.categories_mappings,
            [{"local_category_id": cat, "global_category_id": cat} for cat in global_categories],
        )
        # now categories_mappings will be initialized with the new value
        institution.categories_mappings = []
        notify(ObjectModifiedEvent(institution))
        self.assertListEqual(
            institution.categories_mappings,
            [
                {"local_category_id": "administration", "global_category_id": "administration"},
                {"local_category_id": "animaux", "global_category_id": "animaux"},
                {"local_category_id": "cultes", "global_category_id": "cultes"},
                {"local_category_id": "finances", "global_category_id": "finances"},
            ],
        )
        # only matching ids are kept
        institution.delib_categories = {
            "massa": "quis",
            "vitae": "vel",
            "animaux": "Cat2",
            "tortor": "eros",
            "condimentum": "donec",
            "cultes": "Cat3",
            "lacinia": "ac",
        }
        institution.categories_mappings = []
        notify(ObjectModifiedEvent(institution))
        self.assertListEqual(
            institution.categories_mappings,
            [
                {"local_category_id": "animaux", "global_category_id": "animaux"},
                {"local_category_id": "cultes", "global_category_id": "cultes"},
            ],
        )
