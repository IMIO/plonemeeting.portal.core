from AccessControl import Unauthorized
from plone import api
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
        self.logout()
        self.assertEqual(api.content.get_state(self.private_publication), "private")
        self.private_publication.restrictedTraverse("@@view")



        self.login_as_manager()
        view = self.private_publication.restrictedTraverse("@@view")
        self.assertTrue(view())

        self.login_as_decisions_manager()
        view = self.private_publication.restrictedTraverse("@@view")
        self.assertTrue(view())

        self.login_as_publications_manager()
        view = self.private_publication.restrictedTraverse("@@view")
        self.assertTrue(view())

    def test_planned_publication_view(self):
        self.assertEqual(api.content.get_state(self.planned_publication), "planned")
        view = self.item.restrictedTraverse("@@view")
        self.assertTrue(view())

        self.login_as_manager()
        view = self.item.restrictedTraverse("@@view")
        self.assertTrue(view())

        self.login_as_decisions_manager()
        view = self.item.restrictedTraverse("@@view")
        self.assertTrue(view())

        self.login_as_publications_manager()
        view = self.item.restrictedTraverse("@@view")
        self.assertTrue(view())

    def test_published_publication_view(self):
        self.assertEqual(api.content.get_state(self.published_publication), "published")
        view = self.item.restrictedTraverse("@@view")
        self.assertTrue(view())

        self.login_as_manager()
        view = self.item.restrictedTraverse("@@view")
        self.assertTrue(view())

        self.login_as_decisions_manager()
        view = self.item.restrictedTraverse("@@view")
        self.assertTrue(view())

        self.login_as_publications_manager()
        view = self.item.restrictedTraverse("@@view")
        self.assertTrue(view())


    def test_unpublished_publication_view(self):
        self.assertEqual(api.content.get_state(self.unpublished_publication), "unpublished")
        view = self.item.restrictedTraverse("@@view")
        self.assertTrue(view())

        self.login_as_manager()
        view = self.item.restrictedTraverse("@@view")
        self.assertTrue(view())

        self.login_as_decisions_manager()
        view = self.item.restrictedTraverse("@@view")
        self.assertTrue(view())

        self.login_as_publications_manager()
        view = self.item.restrictedTraverse("@@view")
        self.assertTrue(view())
