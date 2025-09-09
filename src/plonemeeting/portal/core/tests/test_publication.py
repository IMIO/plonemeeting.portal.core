from collective.timestamp.interfaces import ITimeStamper
from datetime import datetime
from datetime import timedelta
from DateTime import DateTime
from imio.helpers.content import uuidToCatalogBrain
from pathlib import Path
from plone import api
from plone.dexterity.events import EditCancelledEvent
from plone.locking.interfaces import ILockable
from plone.namedfile.file import NamedBlobFile
from plone.testing.zope import Browser
from plonemeeting.portal.core.tests import PM_ADMIN_USER
from plonemeeting.portal.core.tests import PM_USER_PASSWORD
from plonemeeting.portal.core.tests.portal_test_case import PmPortalDemoFunctionalTestCase
from Products.CMFCore.WorkflowCore import WorkflowException
from unittest import mock
from zExceptions import Redirect
from zExceptions import Unauthorized
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent

import pytz
import transaction
import xml.etree.ElementTree as ET
import zipfile


class TestPublicationView(PmPortalDemoFunctionalTestCase):

    def setUp(self):
        super().setUp()
        self.private_publication = self.institution.publications["publication-28"]
        self.planned_publication = self.institution.publications["publication-30"]
        self.published_publication = self.institution.publications["publication-1"]
        self.unpublished_publication = self.institution.publications["publication-27"]
        mock_tsr_path = Path(__file__).parent / "resources/mock_tsr_file.tsr"
        with open(mock_tsr_path, "rb") as f:
            self.published_publication.timestamp = NamedBlobFile(data=f.read(), filename="timestamp.tsr")
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

        # Testing some getters
        self.published_publication.authority_date = DateTime("2025/09/04")
        self.published_publication.expired_authority_date = DateTime("2025/10/04")
        view = self.published_publication.restrictedTraverse("@@view")
        self.assertEqual(view.get_authority_date(), "04/09/2025")
        self.assertEqual(view.get_expired_authority_date(), "04/10/2025")

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

    def test_timestamp_asic_file(self):
        self.logout()
        request = getattr(self, "request", None) or getattr(self.portal, "REQUEST")
        view = self.published_publication.restrictedTraverse("@@asic-archive")
        tmp_fp = view()  # expected: file-like object (e.g., _io.FileIO) pointing at a temp .asice
        try:
            # Basic checks
            self.assertTrue(hasattr(tmp_fp, "read"), "Returned object must be file-like")
            readable = getattr(tmp_fp, "readable", lambda: True)()
            self.assertTrue(readable, "Returned file-like must be readable")
            fname = getattr(tmp_fp, "name", "")
            self.assertTrue(str(fname), "Temporary file should have a name")
            self.assertTrue(str(fname).endswith(".asice"), f"Expected '.asice' file, got {fname!r}")
            mode = getattr(tmp_fp, "mode", "rb")
            self.assertIn("b", mode, "Temp file should be opened in binary mode")

            # Validate it opens as a ZIP and has ASiC structure
            with zipfile.ZipFile(tmp_fp) as zf:
                names = zf.namelist()
                self.assertTrue(names, "ASiC container should contain at least one entry")
                # ASiC containers typically include a META-INF directory with signature data
                self.assertTrue(
                    any(n.startswith("META-INF/") for n in names),
                    "ASiC container should include META-INF/",
                )
                # Ensure no corrupt members
                self.assertIsNone(zf.testzip(), "ZIP members should not be corrupted")

                self.assertIn("META-INF/ASiCManifest001.xml", names)
                self.assertIn("META-INF/timestamp.tst", names)

                manifest_bytes = zf.read("META-INF/ASiCManifest001.xml")
                self.assertGreater(len(manifest_bytes), 50, "Manifest should not be tiny")
                try:
                    root = ET.fromstring(manifest_bytes)
                except ET.ParseError as e:
                    self.fail(f"ASiC manifest is not well-formed XML: {e}")

                uris = {el.get("URI") for el in root.iter() if "URI" in el.attrib}
                self.assertTrue(uris, "Manifest should contain at least one URI reference")
                self.assertTrue(
                    any(u and (u.endswith("archive.zip") or u.endswith("mimetype")) for u in uris),
                    "Manifest should reference payload objects (archive.zip and/or mimetype).",
                )
                ts_bytes = zf.read("META-INF/timestamp.tst")
                self.assertGreater(len(ts_bytes), 120, "Timestamp token should be non-trivial in size")

                # Should be binary (DER), not decodable as UTF-8 text
                with self.assertRaises(UnicodeDecodeError):
                    ts_bytes.decode("utf-8")

                # DER-encoded CMS should start with ASN.1 SEQUENCE (0x30)
                self.assertEqual(
                    ts_bytes[0], 0x30, "timestamp.tst should be DER: first byte must be ASN.1 SEQUENCE (0x30)"
                )

        finally:
            try:
                tmp_fp.close()
            except Exception:
                pass

        # Response header checks (content-type/disposition) set by the view
        response = request.RESPONSE
        ctype = response.getHeader("Content-Type")
        # Allow a few common types seen for ASiC containers
        self.assertIn(
            ctype,
            (
                "application/vnd.etsi.asic-e+zip",
                "application/vnd.etsi.asic-e",
                "application/zip",
                "application/octet-stream",
            ),
            f"Unexpected Content-Type: {ctype!r}",
        )

        disp = response.getHeader("Content-Disposition")
        self.assertIsNotNone(disp, "Content-Disposition should be set for download")
        self.assertIn("attachment", disp.lower(), "Download should be served as attachment")
        self.assertRegex(
            disp,
            r'filename="?[^"]+\.asice"?',
            f"Content-Disposition should specify an .asice filename, got {disp!r}",
        )
        self.assertNotIn(response.getStatus(), (301, 302, 401, 403), "Anonymous should be allowed to download")
        self.assertIsNone(response.getHeader("location"), "Should not redirect")

        with self.assertRaises(Unauthorized):
            view = self.unpublished_publication.restrictedTraverse("@@asic-archive")
            view()

        self.login_as_publications_manager()
        self.unpublished_publication.enable_timestamping = False
        self.unpublished_publication.timestamp = None
        view = self.unpublished_publication.restrictedTraverse("@@asic-archive")
        self.assertEqual(view(), "Missing required files for ASiC generation.")

        self.unpublished_publication.enable_timestamping = True
        self.unpublished_publication.timestamp = NamedBlobFile(data=b"fake", filename="timestamp.tsr")
        view = self.unpublished_publication.restrictedTraverse("@@asic-archive")
        with self.assertRaises(ValueError):
            view()

    def test_timestamp_asic_file(self):
        self.logout()
        request = getattr(self, "request", None) or getattr(self.portal, "REQUEST")
        view = self.published_publication.restrictedTraverse("@@asic-archive")
        tmp_fp = view()  # expected: file-like object (e.g., _io.FileIO) pointing at a temp .asice
        try:
            # Basic checks
            self.assertTrue(hasattr(tmp_fp, "read"), "Returned object must be file-like")
            readable = getattr(tmp_fp, "readable", lambda: True)()
            self.assertTrue(readable, "Returned file-like must be readable")
            fname = getattr(tmp_fp, "name", "")
            self.assertTrue(str(fname), "Temporary file should have a name")
            self.assertTrue(str(fname).endswith(".asice"), f"Expected '.asice' file, got {fname!r}")
            mode = getattr(tmp_fp, "mode", "rb")
            self.assertIn("b", mode, "Temp file should be opened in binary mode")

            # Validate it opens as a ZIP and has ASiC structure
            with zipfile.ZipFile(tmp_fp) as zf:
                names = zf.namelist()
                self.assertTrue(names, "ASiC container should contain at least one entry")
                # ASiC containers typically include a META-INF directory with signature data
                self.assertTrue(
                    any(n.startswith("META-INF/") for n in names),
                    "ASiC container should include META-INF/",
                )
                # Ensure no corrupt members
                self.assertIsNone(zf.testzip(), "ZIP members should not be corrupted")

                self.assertIn("META-INF/ASiCManifest001.xml", names)
                self.assertIn("META-INF/timestamp.tst", names)

                manifest_bytes = zf.read("META-INF/ASiCManifest001.xml")
                self.assertGreater(len(manifest_bytes), 50, "Manifest should not be tiny")
                try:
                    root = ET.fromstring(manifest_bytes)
                except ET.ParseError as e:
                    self.fail(f"ASiC manifest is not well-formed XML: {e}")

                uris = {el.get("URI") for el in root.iter() if "URI" in el.attrib}
                self.assertTrue(uris, "Manifest should contain at least one URI reference")
                self.assertTrue(
                    any(u and (u.endswith("archive.zip") or u.endswith("mimetype")) for u in uris),
                    "Manifest should reference payload objects (archive.zip and/or mimetype).",
                )
                ts_bytes = zf.read("META-INF/timestamp.tst")
                self.assertGreater(len(ts_bytes), 120, "Timestamp token should be non-trivial in size")

                # Should be binary (DER), not decodable as UTF-8 text
                with self.assertRaises(UnicodeDecodeError):
                    ts_bytes.decode("utf-8")

                # DER-encoded CMS should start with ASN.1 SEQUENCE (0x30)
                self.assertEqual(
                    ts_bytes[0], 0x30, "timestamp.tst should be DER: first byte must be ASN.1 SEQUENCE (0x30)"
                )

        finally:
            try:
                tmp_fp.close()
            except Exception:
                pass

        # Response header checks (content-type/disposition) set by the view
        response = request.RESPONSE
        ctype = response.getHeader("Content-Type")
        # Allow a few common types seen for ASiC containers
        self.assertIn(
            ctype,
            (
                "application/vnd.etsi.asic-e+zip",
                "application/vnd.etsi.asic-e",
                "application/zip",
                "application/octet-stream",
            ),
            f"Unexpected Content-Type: {ctype!r}",
        )

        disp = response.getHeader("Content-Disposition")
        self.assertIsNotNone(disp, "Content-Disposition should be set for download")
        self.assertIn("attachment", disp.lower(), "Download should be served as attachment")
        self.assertRegex(
            disp,
            r'filename="?[^"]+\.asice"?',
            f"Content-Disposition should specify an .asice filename, got {disp!r}",
        )
        self.assertNotIn(response.getStatus(), (301, 302, 401, 403), "Anonymous should be allowed to download")
        self.assertIsNone(response.getHeader("location"), "Should not redirect")

        with self.assertRaises(Unauthorized):
            view = self.unpublished_publication.restrictedTraverse("@@asic-archive")
            view()

        self.login_as_publications_manager()
        self.unpublished_publication.enable_timestamping = False
        self.unpublished_publication.timestamp = None
        view = self.unpublished_publication.restrictedTraverse("@@asic-archive")
        self.assertEqual(view(), "Missing required files for ASiC generation.")

        self.unpublished_publication.enable_timestamping = True
        self.unpublished_publication.timestamp = NamedBlobFile(data=b"fake", filename="timestamp.tsr")
        view = self.unpublished_publication.restrictedTraverse("@@asic-archive")
        with self.assertRaises(ValueError):
            view()

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
        pub.restrictedTraverse("@@edit")
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
            file=NamedBlobFile(data=b"New file content", filename="new_file.txt"),
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

        with (
            mock.patch("plonemeeting.portal.core.browser.publication.IStatusMessage") as status_cls,
            mock.patch("plonemeeting.portal.core.browser.publication.notify") as notify,
        ):
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
        browser.getControl(name="form.widgets.IBasic.title").value = "MyTitle"
        browser.getControl("Save").click()
        self.assertTrue(browser.url.endswith(self.private_publication.absolute_url()))
        self.assertTrue("MyTitle" in browser.contents)

    def test_edit_cancel_publication(self):
        self.login_as_publications_manager()
        pub = self.private_publication
        form = pub.restrictedTraverse("@@edit")
        form.update()

        with (
            mock.patch("plonemeeting.portal.core.browser.publication.IStatusMessage") as status_cls,
            mock.patch("plonemeeting.portal.core.browser.publication.notify") as notify,
        ):
            form.handleCancel(form, action=None)

        status_cls.return_value.addStatusMessage.assert_called_once_with("Edit cancelled", "info")
        self.assertEqual(form.request.response.getHeader("location"), pub.absolute_url())

        dispatched = notify.call_args[0][0]
        self.assertIsInstance(dispatched, EditCancelledEvent)
        self.assertIs(dispatched.object, pub)

    def test_publication_can_be_published_directly_from_private(self):
        self.login_as_publications_manager()
        # Given a private publication with a future effective date
        future_pub = self.private_publication
        future_pub.setEffectiveDate(DateTime("2099/01/01"))
        # When we try to publish it
        self.workflow.doActionFor(future_pub, "publish")
        self.assertEqual(api.content.get_state(future_pub), "published")
        self.assertIsNotNone(future_pub.effective_date)
        # The effective date is set to now
        self.assertAlmostEqual(future_pub.effective().asdatetime(), datetime.now(pytz.UTC), delta=timedelta(seconds=10))

        # Given a past publication
        past_pub = api.content.create(
            container=self.institution.publications,
            type="Publication",
            title="Test Publication",
            enable_timestamping=True,
            effective_date=DateTime("1901/01/01"),
        )
        # planning it shouldn't be possible
        with self.assertRaises(WorkflowException):
            self.workflow.doActionFor(past_pub, "plan")

        # when we try to publish it
        self.workflow.doActionFor(past_pub, "publish")
        self.assertEqual(api.content.get_state(past_pub), "published")
        self.assertIsNotNone(past_pub.effective_date)
        # The effective date is set to now
        self.assertAlmostEqual(past_pub.effective().asdatetime(), datetime.now(pytz.UTC), delta=timedelta(seconds=10))

        # Given a past publication without timestamping enabled
        past_pub_no_ts = api.content.create(
            container=self.institution.publications,
            type="Publication",
            title="Test Publication No Timestamping",
            enable_timestamping=False,
            effective_date=DateTime("1901/01/01"),
        )
        # planning it shouldn't be possible
        with self.assertRaises(WorkflowException):
            self.workflow.doActionFor(past_pub_no_ts, "plan")
        # when we try to publish it
        self.workflow.doActionFor(past_pub_no_ts, "publish")
        self.assertEqual(api.content.get_state(past_pub_no_ts), "published")
        self.assertIsNotNone(past_pub_no_ts.effective_date)
        # The effective date is kept
        self.assertEqual(past_pub_no_ts.effective_date, DateTime("1901/01/01"))
