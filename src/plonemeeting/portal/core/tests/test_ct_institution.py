# -*- coding: utf-8 -*-
from plone import api
from plone.api.content import get_state
from plone.api.exc import InvalidParameterError
from plone.dexterity.interfaces import IDexterityFTI
from plonemeeting.portal.core.content.institution import IInstitution
from plonemeeting.portal.core.tests.portal_test_case import PmPortalTestCase
from plonemeeting.portal.core.utils import format_institution_managers_group_id
from zope.component import createObject
from zope.component import queryUtility


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

        meetings_folder, decisions_folder = institution.listFolderContents()[0:2]
        self.assertEqual(get_state(meetings_folder), 'private')
        self.assertEqual(get_state(decisions_folder), 'private')

        api.content.transition(institution, to_state='published')
        self.assertEqual(get_state(institution), 'published')
        self.assertEqual(get_state(meetings_folder), 'published')
        self.assertEqual(get_state(decisions_folder), 'published')
        self.assertEqual(get_state(meeting), 'private')

        api.content.transition(institution, to_state='private')
        self.assertEqual(get_state(institution), 'private')
        self.assertEqual(get_state(meetings_folder), 'private')
        self.assertEqual(get_state(decisions_folder), 'private')
        self.assertEqual(get_state(meeting), 'private')

        agenda_folder = api.content.create(type="Folder",
                                           title="Agenda",
                                           container=institution)
        # meeting are ignored when publishing the institution
        # but put back to private if the institution goes back in private
        api.content.transition(institution, to_state='published')
        self.assertEqual(get_state(institution), 'published')
        self.assertEqual(get_state(meetings_folder), 'published')
        self.assertEqual(get_state(decisions_folder), 'published')
        self.assertEqual(get_state(agenda_folder), 'published')
        self.assertEqual(get_state(meeting), 'private')

        api.content.transition(meeting, to_state='decision')

        api.content.transition(institution, to_state='private')
        self.assertEqual(get_state(institution), 'private')
        self.assertEqual(get_state(meetings_folder), 'private')
        self.assertEqual(get_state(decisions_folder), 'private')
        self.assertEqual(get_state(agenda_folder), 'private')
        self.assertEqual(get_state(meeting), 'private')
