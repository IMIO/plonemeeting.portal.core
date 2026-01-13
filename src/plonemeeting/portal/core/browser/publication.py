from ZODB.blob import Blob
from asn1crypto import tsp
from collective.timestamp.interfaces import ITimeStamper
from plone import api
from plone.app.content.browser.content_status_modify import ContentStatusModifyView
from plone.app.uuid.utils import uuidToObject
from plone.dexterity.browser.add import DefaultAddView
from plone.dexterity.browser.view import DefaultView
from plone.dexterity.events import EditCancelledEvent
from plone.memoize.view import memoize
from plone.namedfile import NamedBlobFile
from plone.namedfile.field import NamedBlobImage, NamedImage, NamedFile
from plone.namedfile.interfaces import INamedFileField, INamedImageField
from plonemeeting.portal.core import _
from plonemeeting.portal.core.behaviors.supersede import SupersedeAdapter
from plonemeeting.portal.core.browser import BaseAddForm
from plonemeeting.portal.core.browser import BaseEditForm
from Products.CMFCore.permissions import ModifyPortalContent
from Products.CMFCore.utils import _checkPermission
from Products.Five import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from plonemeeting.portal.core.content.publication import IPublication
from z3c.form import button
from z3c.form.interfaces import IDataManager, IDataConverter
from zope.component import getMultiAdapter, getUtility
from zope.event import notify
from ZPublisher.Iterators import filestream_iterator

import copy
import os
import pathlib
import tempfile
import zipfile

from zope.interface import Interface


class PublicationForm:
    zope_admin_fieldsets = ["settings"]
    fieldsets_order = ["dates", "authority", "timestamp", "relationships", "categorization", "settings"]


class AddForm(PublicationForm, BaseAddForm):
    """Override to reorder and filter out fieldsets."""

    COPY_BLACKLIST = {
        "id",
        "decision_date",
        "IPublication.effective",
        "IPublication.expires",
        "timestamp",
        "timestamped_file",
        "ISupersede.supersede"
    }

    def _is_cloning(self):
        return "_copy_from" in self.request.form

    def _apply_copy_blacklist(self):
        for widget in self._iter_all_widgets():
            field = getattr(widget, "field", None)
            if field is None:
                continue
            field_name = widget.__name__
            print(field_name)
            if field_name in self.COPY_BLACKLIST:
                # Clear the value so it behaves like a normal add form
                widget.value = field.missing_value

    def update(self):
        super().update()
        if self._is_cloning() and self.request.get("REQUEST_METHOD") == "GET":
            self._apply_copy_blacklist()
            return
        # Set default texts from institution
        if self.request.get("REQUEST_METHOD") == "GET":
            self.widgets['text'].value = copy.deepcopy(self.institution.default_publication_text)
            self.widgets['consultation_text'].value = copy.deepcopy(self.institution.default_publication_consultation_text)

    def getContent(self):
        if not self._is_cloning():
            return super().getContent()
        copy_uid = self.request.get("_copy_from")
        source = uuidToObject(copy_uid) if copy_uid else None
        # We'll trick Plone into thinking we're in a different context like the edit form does.
        self.ignoreContext = False
        return source

    #
    # def update(self):
    #     super().update()
    #     if "_copy_from" in self.request and "_copy_from" not in self.request.form:
    #         self.request.form["_copy_from"] = self.request.get("_copy_from")
    #     source_uid = self.request.get("_copy_from")
    #     if not source_uid:
    #         return
    #     source = uuidToObject(source_uid)
    #     if not source:
    #         return
    #
    #     self._prefill_widgets_from(source)
    #
    # def create(self, data):
    #     import pdb; pdb.set_trace() # TODO: REMOVE BEFORE FLIGHT ---------------------------------------------------
    #     source_uid = self.request.get("_copy_from")
    #     source = uuidToObject(source_uid) if source_uid else None
    #
    #     if source:
    #         for f in self.fields.values():
    #             name = f.__name__
    #             field = f.field
    #
    #             if not (INamedFileField.providedBy(field) or INamedImageField.providedBy(field)):
    #                 continue
    #
    #             src_val = getattr(source, name, None)
    #             if not src_val:
    #                 continue
    #
    #             current = data.get(name, field.missing_value)
    #
    #             # If the user did NOT upload a replacement, keep the source file by copying it
    #             if current in (None, field.missing_value):
    #                 data[name] = self.clone_namedfile(src_val)
    #
    #     return super().create(data)
    #
    # @staticmethod
    # def clone_namedfile(value):
    #     """Make a real copy (new instance) of a Named(File|Image|Blob*)."""
    #     if value is None:
    #         return None
    #
    #     # NOTE: value.data reads into memory; for very large blobs you may prefer streaming.
    #     data = value.data
    #     filename = getattr(value, "filename", None)
    #     contentType = getattr(value, "contentType", None)
    #
    #     if isinstance(value, NamedBlobImage):
    #         return NamedBlobImage(data=data, filename=filename, contentType=contentType)
    #     if isinstance(value, NamedImage):
    #         return NamedImage(data=data, filename=filename, contentType=contentType)
    #     if isinstance(value, NamedBlobFile):
    #         return NamedBlobFile(data=data, filename=filename, contentType=contentType)
    #     if isinstance(value, NamedFile):
    #         return NamedFile(data=data, filename=filename, contentType=contentType)
    #
    #     # Fallback: try same class signature
    #     return value.__class__(data=data, filename=filename, contentType=contentType)
    #
    # def _iter_all_widgets(self):
    #     # main fieldset
    #     for w in getattr(self, "widgets", {}).values():
    #         yield w
    #     # groups/fieldsets created by behaviors / form extenders
    #     for group in self.groups:
    #         for w in group.widgets.values():
    #             yield w
    #
    # def _prefill_widgets_from(self, source):
    #     for widget in self._iter_all_widgets():
    #         field = getattr(widget, "field", None)
    #         if field is None:
    #             continue
    #
    #         # Skip invisible / non-input widgets (usually safe)
    #         if getattr(widget, "mode", None) != "input":
    #             continue
    #
    #         # If the user already submitted something once (validation error),
    #         if widget.name in self.request.form:
    #             continue
    #
    #         if getattr(field, "readonly", False):
    #             continue
    #
    #         # A stable way to identify a field is its full dotted name if available,
    #         # otherwise fall back to widget.__name__ (field name in the schema).
    #         field_id = getattr(field, "__name__", None) or widget.__name__
    #
    #         if field_id in self.COPY_BLACKLIST or widget.__name__ in self.COPY_BLACKLIST:
    #             continue
    #
    #         # Read the python value from the source using Plone’s normal storage rules
    #         dm = getMultiAdapter((source, field), IDataManager)
    #         value = dm.get()
    #
    #         if value == field.missing_value:
    #             continue
    #
    #         # Convert python value -> widget value (handles richtext, relations, dates, etc.)
    #         converter = IDataConverter(widget)
    #         widget.value = converter.toWidgetValue(value)


class PublicationAdd(PublicationForm, DefaultAddView):
    form = AddForm


class EditForm(PublicationForm, BaseEditForm):
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

    def _get_linked_obj_infos(self, obj):
        url = obj.absolute_url()
        try:
            title = obj.Title()
        except Exception:
            title = getattr(obj, "title", url)

        effective = obj.effective()

        try:
            description = obj.Description() or ""
        except Exception:
            description = getattr(obj, "description", "") or ""

        try:
            review_state = api.content.get_state(obj=obj)
        except Exception:
            review_state = None

        portal_type = getattr(obj, "portal_type", "")
        if portal_type == "Item":
            portal_type = "Decision"

        return {
            "title": title,
            "url": url,
            "description": description,
            "portal_type": portal_type,
            "current": self.context == obj,
            "effective": self.context.toLocalizedTime(effective, long_format=False)
            if effective
            else "",
            "review_state": review_state or "",
        }

    @memoize
    def timeline(self):
        supersede_adapter = SupersedeAdapter(self.context)
        superseding_items = supersede_adapter.superseded_by_items()
        current_item = self.context
        superseded_items = supersede_adapter.supersedes_items()
        objs_timeline = list(reversed(superseding_items)) + [current_item] + superseded_items
        results = []
        for obj in objs_timeline:
            if not api.user.has_permission('View', obj=obj):
                continue
            results.append(
                self._get_linked_obj_infos(obj)
            )
        return results

    def has_timeline(self):
        return len(self.timeline()) > 1

    @memoize
    def related_items(self):
        """Return list of related items."""
        return [self._get_linked_obj_infos(rel.to_object) for rel in
                api.relation.get(source=self.context, relationship="relatedItems")]

    def has_related_items(self):
        return bool(self.related_items())


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
