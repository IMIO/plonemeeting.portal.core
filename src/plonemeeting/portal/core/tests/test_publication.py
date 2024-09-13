from AccessControl import Unauthorized
from plone import api
from plone.locking.interfaces import ILockable
from plonemeeting.portal.core.tests.portal_test_case import PmPortalDemoFunctionalTestCase

class TestPublicationView(PmPortalDemoFunctionalTestCase):

    def setUp(self):
        super().setUp()
        self.private_publication = self.institution.publications["publication-28"]
        self.planned_publication = self.institution.publications["publication-30"]
        self.published_publication = self.institution.publications["publication-1"]
        self.unpublished_publication = self.institution.publications["publication-27"]
        self.login_as_test()

    def test_private_publication_view(self):
        self.assertEqual(api.content.get_state(self.private_publication), "private")
        self.logout()
        with self.assertRaises(Unauthorized):
            self.private_publication.restrictedTraverse("@@view")
            self.private_publication.restrictedTraverse("@@edit")

        self.login_as_decisions_manager()
        view = self.private_publication.restrictedTraverse("@@view")
        self.assertTrue(view())
        with self.assertRaises(Unauthorized):
            self.private_publication.restrictedTraverse("@@edit")

        self.login_as_publications_manager()
        view = self.private_publication.restrictedTraverse("@@view")
        self.assertTrue(view())
        view = self.private_publication.restrictedTraverse("@@edit")
        self.assertTrue(view())
        ILockable(self.private_publication).unlock()

        self.login_as_manager()
        view = self.private_publication.restrictedTraverse("@@view")
        self.assertTrue(view())
        view = self.private_publication.restrictedTraverse("@@edit")
        self.assertTrue(view())

    def test_planned_publication_view(self):
        self.assertEqual(api.content.get_state(self.planned_publication), "planned")
        self.logout()
        with self.assertRaises(Unauthorized):
            self.planned_publication.restrictedTraverse("@@view")
            self.planned_publication.restrictedTraverse("@@edit")

        self.login_as_decisions_manager()
        view = self.item.restrictedTraverse("@@view")
        self.assertTrue(view())
        with self.assertRaises(Unauthorized):
            self.planned_publication.restrictedTraverse("@@edit")

        self.login_as_publications_manager()
        view = self.planned_publication.restrictedTraverse("@@view")
        self.assertTrue(view())
        view = self.planned_publication.restrictedTraverse("@@edit")
        self.assertTrue(view())
        ILockable(self.planned_publication).unlock()

        self.login_as_manager()
        view = self.planned_publication.restrictedTraverse("@@view")
        self.assertTrue(view())
        view = self.planned_publication.restrictedTraverse("@@edit")
        self.assertTrue(view())

    def test_published_publication_view(self):
        self.assertEqual(api.content.get_state(self.published_publication), "published")
        self.logout()
        self.published_publication.restrictedTraverse("view")
        with self.assertRaises(Unauthorized):
            self.published_publication.restrictedTraverse("@@edit")

        self.login_as_decisions_manager()
        view = self.published_publication.restrictedTraverse("@@view")
        self.assertTrue(view())
        with self.assertRaises(Unauthorized):
            self.published_publication.restrictedTraverse("@@edit")

        self.login_as_publications_manager()
        view = self.published_publication.restrictedTraverse("@@view")
        self.assertTrue(view())
        with self.assertRaises(Unauthorized):
            self.published_publication.restrictedTraverse("@@edit")

        self.login_as_manager()
        view = self.published_publication.restrictedTraverse("@@view")
        self.assertTrue(view())
        view = self.published_publication.restrictedTraverse("@@edit")
        self.assertTrue(view())

    def test_unpublished_publication_view(self):
        self.assertEqual(api.content.get_state(self.unpublished_publication), "unpublished")
        self.logout()
        with self.assertRaises(Unauthorized):
            self.unpublished_publication.restrictedTraverse("@@view")

        self.login_as_decisions_manager()
        view = self.unpublished_publication.restrictedTraverse("@@view")
        self.assertTrue(view())
        with self.assertRaises(Unauthorized):
            self.unpublished_publication.restrictedTraverse("@@edit")

        self.login_as_publications_manager()
        view = self.unpublished_publication.restrictedTraverse("@@view")
        self.assertTrue(view())
        view = self.unpublished_publication.restrictedTraverse("@@edit")
        self.assertTrue(view())
        ILockable(self.unpublished_publication).unlock()


        self.login_as_manager()
        view = self.unpublished_publication.restrictedTraverse("@@view")
        self.assertTrue(view())
        view = self.unpublished_publication.restrictedTraverse("@@edit")
        self.assertTrue(view())
