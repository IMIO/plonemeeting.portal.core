from AccessControl import Unauthorized
from DateTime import DateTime
from collective.timestamp.interfaces import ITimeStamper
from imio.helpers.content import uuidToCatalogBrain
from plone import api
from plone.locking.interfaces import ILockable
from plone.namedfile.file import NamedBlobFile
from plonemeeting.portal.core.tests.portal_test_case import PmPortalDemoFunctionalTestCase


class TestPublicationView(PmPortalDemoFunctionalTestCase):

    def setUp(self):
        super().setUp()
        self.private_publication = self.institution.publications["publication-28"]
        self.planned_publication = self.institution.publications["publication-30"]
        self.published_publication = self.institution.publications["publication-1"]
        self.published_publication.timestamp = NamedBlobFile(data=b"dummy", filename="timestamp.tsr")
        self.unpublished_publication = self.institution.publications["publication-27"]
        self.login_as_test()

    def test_publication_add_form(self):
        self.login_as_publications_manager()
        add_form = self.institution.publications.restrictedTraverse("++add++Publication")
        self.assertEqual(add_form.form_instance.portal_type, "Publication")
        add_form() # should not raise an exception

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
        with self.assertRaises(Unauthorized):
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

    def test_published_publication_is_timestamped(self):
        self.login_as_publications_manager()
        pub = self.private_publication
        # may be published only if no effectiveDate
        timestamper = ITimeStamper(pub)
        pub.setEffectiveDate(None)
        pub.reindexObject(idxs=timestamper._effective_related_indexes())
        # publication is not timestamped for now
        self.assertFalse(timestamper.is_timestamped())
        self.assertTrue(timestamper.is_timestampable())
        brain = uuidToCatalogBrain(pub.UID())
        indexed = self.catalog.getIndexDataForRID(brain.getRID())
        # 1044622740 is equivalent to "None"
        self.assertEqual(indexed["effective"], 1044622740)
        self.assertEqual(indexed["year"], "")
        # publish so publication is timestamped
        self.workflow.doActionFor(pub, "publish")
        self.assertTrue(timestamper.is_timestamped())
        self.assertFalse(timestamper.is_timestampable())
        # effective has been reindexed
        brain = uuidToCatalogBrain(pub.UID())
        indexed = self.catalog.getIndexDataForRID(brain.getRID())
        self.assertNotEqual(indexed["effective"], 1044622740)
        self.assertEqual(indexed["year"], str(pub.effective().year()))

    def test_effective_date_publication_not_timestamped(self):
        self.login_as_publications_manager()
        pub = self.private_publication
        pub.enable_timestamping = False
        pub.setEffectiveDate(None)
        self.workflow.doActionFor(pub, "publish")
        self.assertIsNotNone(pub.effective_date)
        self.assertEqual(round(DateTime() - pub.effective_date), 0)
        self.workflow.doActionFor(pub, "unpublish")
        pub.setEffectiveDate(DateTime("1999/01/01"))
        self.workflow.doActionFor(pub, "publish")
        self.assertIn("1999-01-01", pub.EffectiveDate())

    def test_timestamp_files_are_downloadable_by_anons(self):
        self.logout()
        download_view = self.published_publication.restrictedTraverse("@@download")
        download_view = download_view.publishTraverse(self.portal.REQUEST, "timestamp")
        # Avoid to call the view (__call__) as it streams the file and not close it when in unit tests
        self.assertEqual(type(download_view._getFile()), NamedBlobFile)
        download_view = download_view.publishTraverse(self.portal.REQUEST, "timestamped_file")
        self.assertEqual(type(download_view._getFile()), NamedBlobFile)
