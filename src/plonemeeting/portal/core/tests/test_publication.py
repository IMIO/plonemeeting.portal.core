from unittest import mock

import Testing
import transaction
from zExceptions import Unauthorized, Redirect
from collective.timestamp.interfaces import ITimeStamper
from DateTime import DateTime
from imio.helpers.content import uuidToCatalogBrain
from plone import api
from plone.dexterity.events import EditCancelledEvent
from plone.locking.interfaces import ILockable
from plone.namedfile.file import NamedBlobFile
from plonemeeting.portal.core.tests import PM_ADMIN_USER, PM_USER_PASSWORD
from plonemeeting.portal.core.tests.portal_test_case import PmPortalDemoFunctionalTestCase
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent
from plone.testing.zope import Browser

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
        add_form()  # should not raise an exception

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

        self.login_as_admin()
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

        self.login_as_admin()
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

        self.login_as_admin()
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

        self.login_as_admin()
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

    def test_timestamp_invalidation(self):
        self.login_as_publications_manager()
        pub = self.published_publication
        timestamper = ITimeStamper(pub)
        self.assertTrue(timestamper.is_timestamped())
        self.assertIsNotNone(pub.timestamp)
        with self.assertRaises(ValueError):
            timestamper.timestamp()  # raises ValueError if publication is already timestamped

        self.workflow.doActionFor(pub, "unpublish")
        # Should still be timestamped
        self.assertTrue(timestamper.is_timestamped())
        self.assertIsNotNone(pub.timestamp)
        # Invalidate timestamp
        pub.restrictedTraverse("@@edit")
        notify(ObjectModifiedEvent(pub))
        self.assertFalse(timestamper.is_timestamped())
        self.assertIsNone(pub.timestamp)

        self.workflow.doActionFor(pub, "publish")
        # Should be timestamped again
        self.assertTrue(timestamper.is_timestamped())
        self.assertIsNotNone(pub.timestamp)
        with self.assertRaises(Unauthorized):
            # Should not be able to edit timestamped publication
            pub.restrictedTraverse("@@edit")

        self.login_as_admin()
        # Manager should be able to edit timestamped publication
        pub.restrictedTraverse('@@edit')
        # But it'll invalidate the timestamp
        notify(ObjectModifiedEvent(pub))
        self.assertFalse(timestamper.is_timestamped())
        self.assertIsNone(pub.timestamp)

        # Now we can timestamp it again
        self.login_as_publications_manager()
        timestamper.timestamp()
        self.assertTrue(timestamper.is_timestamped())

        # If we unpublish and republish, it should be timestamped again
        # with a fresh timestamp
        self.workflow.doActionFor(pub, "unpublish")
        # Should still be timestamped
        self.assertTrue(timestamper.is_timestamped())
        self.assertIsNotNone(pub.timestamp)
        old_timestamp = pub.timestamp

        self.workflow.doActionFor(pub, "publish")
        self.assertTrue(timestamper.is_timestamped())
        self.assertIsNotNone(pub.timestamp)
        self.assertNotEqual(old_timestamp, pub.timestamp)

        # Testing the enable_timestamping feature
        self.workflow.doActionFor(pub, "unpublish")
        pub.enable_timestamping = False
        notify(ObjectModifiedEvent(pub))

        # Should not be timestamped anymore
        self.workflow.doActionFor(pub, "publish")
        self.assertFalse(timestamper.is_timestamped())
        self.assertIsNone(pub.timestamp)

    def test_timestamp_invalidation_with_files(self):
        self.login_as_publications_manager()
        pub = self.published_publication
        timestamper = ITimeStamper(pub)
        self.assertTrue(timestamper.is_timestamped())
        self.assertIsNotNone(pub.timestamp)
        self.workflow.doActionFor(pub, "unpublish")
        # Should still be timestamped
        self.assertTrue(timestamper.is_timestamped())
        self.assertIsNotNone(pub.timestamp)
        # Add a file to the publication
        api.content.create(
            container=pub,
            type="File",
            id="new_file.txt",
            title="New File",
            file=NamedBlobFile(data=b"New file content", filename="new_file.txt")
        )
        self.assertFalse(timestamper.is_timestamped())
        self.assertIsNone(pub.timestamp)

        timestamper.timestamp()
        self.assertTrue(timestamper.is_timestamped())
        self.assertIsNotNone(pub.timestamp)

        # Now if we modify the file, it should invalidate the timestamp
        pub["new_file.txt"].file = NamedBlobFile(data=b"Updated file content", filename="new_file.txt")
        notify(ObjectModifiedEvent(pub["new_file.txt"]))
        self.assertFalse(timestamper.is_timestamped())
        self.assertIsNone(pub.timestamp)


    def test_remove_publication(self):
        self.login_as_decisions_manager()
        self.institution.publications_power_users = ["manager"]
        with self.assertRaises(Unauthorized):
            api.content.delete(self.private_publication)
        self.login_as_publications_manager()
        with self.assertRaises(Redirect):
            # If we have power users, we should not be able to delete the publication
            # As publications manager since he isn't a power user
            api.content.delete(self.private_publication)
        # If we don't have power users, publications manager should be able to delete the publication
        self.institution.publications_power_users = None
        api.content.delete(self.private_publication)

    def test_edit_publication_missing_effective_date(self):
        self.login_as_admin()
        pub = self.planned_publication
        form = pub.restrictedTraverse("@@edit")
        form.update()

        with (mock.patch("plonemeeting.portal.core.browser.publication.IStatusMessage") as status_cls,
              mock.patch("plonemeeting.portal.core.browser.publication.notify") as notify):
            form.handleApply(form, action=None)

        status_cls.return_value.addStatusMessage.assert_called_once()
        msg, level = status_cls.return_value.addStatusMessage.call_args[0]
        self.assertEqual(level, "error")
        self.assertIn("msg_missing_effective_date", msg)

        self.assertIsNone(form.request.response.getHeader("location"))
        notify.assert_not_called()

    def test_edit_publication_success(self):
        transaction.commit()
        browser = Browser(self.layer["app"])
        browser.addHeader("Authorization", f"Basic {PM_ADMIN_USER}:{PM_USER_PASSWORD}")
        browser.open(f"{self.private_publication.absolute_url()}/@@edit")
        browser.getControl(name="form.widgets.IBasic.title").value = (
            "MyTitle"
        )
        browser.getControl("Save").click()
        self.assertTrue(browser.url.endswith(self.private_publication.absolute_url()))
        self.assertTrue("MyTitle" in browser.contents)

    def test_handle_cancel_flashes_and_fires_event(self):
        self.login_as_publications_manager()
        pub = self.private_publication
        form = pub.restrictedTraverse("@@edit")
        form.update()

        with mock.patch(
            "plonemeeting.portal.core.browser.publication.IStatusMessage"
        ) as status_cls, mock.patch(
            "plonemeeting.portal.core.browser.publication.notify"
        ) as notify:
            form.handleCancel(form, action=None)

        status_cls.return_value.addStatusMessage.assert_called_once_with(
            "Edit cancelled", "info"
        )
        self.assertEqual(
            form.request.response.getHeader("location"), pub.absolute_url()
        )

        dispatched = notify.call_args[0][0]
        self.assertIsInstance(dispatched, EditCancelledEvent)
        self.assertIs(dispatched.object, pub)
