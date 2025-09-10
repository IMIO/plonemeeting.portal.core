from asn1crypto import tsp
from collective.timestamp.interfaces import ITimeStamper
from imio.helpers.workflow import get_state_infos
from imio.pyutils.utils import sort_by_indexes
from plone import api
from plone.app.content.browser.content_status_modify import ContentStatusModifyView
from plone.dexterity.browser.add import DefaultAddForm
from plone.dexterity.browser.add import DefaultAddView
from plone.dexterity.browser.edit import DefaultEditForm
from plone.dexterity.browser.view import DefaultView
from plone.dexterity.events import EditCancelledEvent
from plonemeeting.portal.core import _
from Products.CMFCore.permissions import ModifyPortalContent
from Products.CMFCore.utils import _checkPermission
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from z3c.form import button
from zope.event import notify
from ZPublisher.Iterators import filestream_iterator

import os
import pathlib
import tempfile
import zipfile


FIELDSETS_ORDER = ["authority", "dates", "timestamp", "categorization", "settings"]
ADMIN_FIELDSETS = ["settings"]


class AddForm(DefaultAddForm):
    """Override to reorder and filter out fieldsets."""

    def updateFields(self):
        super(AddForm, self).updateFields()
        indexes = [FIELDSETS_ORDER.index(group.__name__) for group in self.groups]
        groups = sort_by_indexes(self.groups, indexes)
        pm = getToolByName(self.context, "portal_membership")
        if not pm.checkPermission("Manage portal", self.context):
            groups = filter(lambda g: g.__name__ not in ADMIN_FIELDSETS, groups)
        self.groups = groups


class PublicationAdd(DefaultAddView):
    form = AddForm


class EditForm(DefaultEditForm):
    """Override to reorder and filter out fieldsets."""

    def render(self):
        """Override to warn about timestamped content.
        We plug ourself here to avoid displaying the warning after the submit."""
        handler = ITimeStamper(self.context)
        if handler.is_timestamped():
            IStatusMessage(self.request).addStatusMessage(_("msg_editing_timestamped_content"), "warning")
        return super().render()

    @button.buttonAndHandler(_("Save"), name="save")
    def handleApply(self, action):
        data, errors = self.extractData()
        if api.content.get_state(self.context) in ("planned", "published") and not data.get("IPublication.effective"):
            IStatusMessage(self.request).addStatusMessage(_("msg_missing_effective_date"), "error")
            return
        super(EditForm, self).handleApply(self, action)

    @button.buttonAndHandler(_("Cancel"), name="cancel")
    def handleCancel(self, action):
        IStatusMessage(self.request).addStatusMessage(_("Edit cancelled"), "info")
        self.request.response.redirect(self.nextURL())
        notify(EditCancelledEvent(self.context))

    def updateFields(self):
        super(EditForm, self).updateFields()
        indexes = [FIELDSETS_ORDER.index(group.__name__) for group in self.groups]
        groups = sort_by_indexes(self.groups, indexes)
        pm = getToolByName(self.context, "portal_membership")
        if not pm.checkPermission("Manage portal", self.context):
            groups = filter(lambda g: g.__name__ not in ADMIN_FIELDSETS, groups)
        self.groups = groups


class PublicationView(DefaultView):
    """ """

    def __call__(self):
        if api.content.get_state(self.context) == "private" and _checkPermission(ModifyPortalContent, self.context):
            if self.context.enable_timestamping is False:
                api.portal.show_message(
                    _("Timestamping is disabled for this element!"), request=self.request, type="warning"
                )
            if (
                self.context.effective_date
                and self.context.effective_date.isPast()
                and self.context.enable_timestamping
            ):
                api.portal.show_message(_("effective_date_in_past_msg"), request=self.request, type="warning")
        return super(PublicationView, self).__call__()

    def get_effective_date(self):
        return self.context.effective_date.strftime("%d/%m/%Y à %H:%M") if self.context.effective_date else "-"

    def get_expiration_date(self):
        return self.context.expiration_date.strftime("%d/%m/%Y à %H:%M") if self.context.expiration_date else "-"

    def get_decision_date(self):
        return self.context.decision_date.strftime("%d/%m/%Y") if self.context.decision_date else "-"

    def get_authority_date(self):
        return self.context.authority_date.strftime("%d/%m/%Y") if self.context.authority_date else "-"

    def get_expired_authority_date(self):
        return self.context.expired_authority_date.strftime("%d/%m/%Y") if self.context.expired_authority_date else "-"

    def get_entry_date(self):
        return self.context.entry_date.strftime("%d/%m/%Y") if self.context.entry_date else "-"

    def get_state_title(self):
        return get_state_infos(self.context)["state_title"]


class PublicationASiCFileView(BrowserView):
    """View to download the ASiC file of a publication."""

    import base64
    import hashlib
    import xml.etree.ElementTree as ET

    NS = {
        "asic": "http://uri.etsi.org/02918/v1.2.1#",
        "xades": "http://uri.etsi.org/01903/v1.3.2#"
    }

    for p, uri in NS.items():
        ET.register_namespace(p, uri)

    def __call__(self):
        """Return the ASiC file as a response."""
        context = self.context

        # Locate the files (adjust field names or logic to your model)
        archive_zip = getattr(context, 'timestamped_file', None)
        tst_file = getattr(context, 'timestamp', None)

        if not archive_zip or not tst_file:
            self.request.response.setStatus(404)
            return "Missing required files for ASiC generation."

        # Save temporary copies
        with tempfile.TemporaryDirectory() as tmpdir:
            archive_path = os.path.join(tmpdir, 'archive.zip')
            tst_path = os.path.join(tmpdir, 'timestamp.tst')
            asice_path = os.path.join(tmpdir, 'output.asice')

            with open(archive_path, 'wb') as f:
                f.write(archive_zip.data)

            with open(tst_path, 'wb') as f:
                f.write(tst_file.data)

            # Build ASiC
            self.make_asice(archive_path, tst_path, asice_path)

            # Serve file
            filename = f"{context.getId()}.asice"
            self.request.response.setHeader("Content-Type", "application/vnd.etsi.asic-e+zip")
            self.request.response.setHeader("Content-Disposition", f'attachment; filename="{filename}"')
            self.request.response.setHeader("Content-Length", str(os.path.getsize(asice_path)))
            return filestream_iterator(asice_path)

    def make_manifest(self, payload_name: str, digest_val: bytes) -> bytes:
        root = self.ET.Element("{%s}ASiCManifest" % self.NS["asic"])
        doi = self.ET.SubElement(root, "{%s}DataObjectInfo" % self.NS["asic"])
        dor = self.ET.SubElement(doi, "{%s}DataObjectReference" % self.NS["asic"], URI=payload_name)
        self.ET.SubElement(
            dor,
            "{%s}DigestMethod" % self.NS["asic"],
            Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"
        )
        self.ET.SubElement(dor, "{%s}DigestValue" % self.NS["asic"]).text = self.base64.b64encode(digest_val).decode()
        return self.ET.tostring(root, encoding="utf-8", xml_declaration=True)

    def tsr_to_tst(self, tsr_path: str, tst_path: str) -> None:
        with open(tsr_path, "rb") as f:
            tsr = tsp.TimeStampResp.load(f.read())
        status = tsr["status"]["status"].native
        if status not in ("granted", "granted_with_mods"):
            raise ValueError(f"TSR not granted (status={status})")
        with open(tst_path, "wb") as f:
            f.write(tsr["time_stamp_token"].dump())

    def make_asice(self, archive_zip: str, tst_file_or_tsr: str, out_asice: str) -> None:
        payload_name = pathlib.Path(archive_zip).name
        with open(archive_zip, "rb") as f:
            sha256 = self.hashlib.sha256(f.read()).digest()
        manifest_xml = self.make_manifest(payload_name, sha256)

        with tempfile.NamedTemporaryFile(suffix=".tst", delete=False) as tmp_tst:
            converted_tst_path = tmp_tst.name
            self.tsr_to_tst(tst_file_or_tsr, converted_tst_path)

        with zipfile.ZipFile(out_asice, "w") as z:
            # Mimetype
            z.writestr("mimetype", b"application/vnd.etsi.asic-e+zip", compress_type=zipfile.ZIP_STORED)

            # Payload
            z.write(archive_zip, arcname=payload_name, compress_type=zipfile.ZIP_DEFLATED)

            # META-INF/ASiCmanifest.xml
            z.writestr("META-INF/ASiCManifest001.xml", manifest_xml, compress_type=zipfile.ZIP_DEFLATED)

            # META-INF/timestamp.tst (converted from .tsr)
            z.write(converted_tst_path, arcname="META-INF/timestamp.tst", compress_type=zipfile.ZIP_DEFLATED)


class PublicationContentStatusModifyView(ContentStatusModifyView):
    """Override to not set a publication date automatically."""

    def editContent(self, obj, effective, expiry):
        """Override to bypass setting effective_date and
        expiration_date upon any workflow transition."""
        return


class TimestampCheckView(BrowserView):
    """A view to validate the publication."""
    pass
