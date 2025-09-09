from AccessControl import ClassSecurityInfo
from collective.timestamp.behaviors.timestamp import ITimestampableDocument
from collective.timestamp.interfaces import ITimeStamper
from DateTime import DateTime
from imio.helpers import EMPTY_DATETIME
from imio.helpers.content import object_values
from plone import api
from plone.app.contenttypes.content import File
from plone.app.contenttypes.interfaces import IFile
from plone.app.dexterity.textindexer import searchable
from plone.app.textfield import RichText
from plone.app.z3cform.widgets.richtext import RichTextFieldWidget
from plone.autoform.directives import order_after
from plone.autoform.directives import read_permission
from plone.autoform.directives import widget
from plone.autoform.directives import write_permission
from plone.dexterity.content import Container
from plone.indexer.decorator import indexer
from plone.namedfile.field import NamedBlobFile
from plone.supermodel import model
from plonemeeting.portal.core import _
from Products.CMFCore.permissions import ManagePortal
from Products.CMFCore.permissions import ModifyPortalContent
from Products.CMFCore.permissions import View
from Products.CMFCore.utils import _checkPermission
from zope import schema
from zope.component import getMultiAdapter
from zope.globalrequest import getRequest
from zope.interface import implementer


class IPublication(model.Schema, IFile, ITimestampableDocument):
    """Marker interface and Dexterity Python Schema for Publication"""

    document_type = schema.Choice(
        vocabulary="plonemeeting.portal.vocabularies.document_types",
        title=_("Document type"),
        required=False,
    )

    category = schema.Choice(
        vocabulary="plonemeeting.portal.vocabularies.global_categories",
        title=_("Category"),
        required=False,
    )

    legislative_authority = schema.Choice(
        vocabulary="plonemeeting.portal.vocabularies.legislative_authorities",
        title=_("Legislative authority"),
        required=False,
    )

    decision_date = schema.Date(
        title=_("Decision date"),
        required=False,
    )

    entry_date = schema.Date(
        title=_("Entry date"),
        required=False,
    )

    consultation_text = RichText(title=_("Hour and place of consultation"), required=False)

    text = RichText(
        title=_("Text"),
        required=False,
    )
    widget("text", RichTextFieldWidget)
    searchable("text")

    model.primary("file")
    file = NamedBlobFile(title="File", accept=("application/pdf",), required=False)

    # Styling fieldset
    model.fieldset(
        "authority",
        label=_("Authority"),
        fields=[
            "subject_to_authority",
            "authority_date",
            "expired_authority_date",
        ],
    )
    subject_to_authority = schema.Bool(
        title=_("Subject to authority?"),
        required=False,
        default=True,
    )

    authority_date = schema.Date(
        title=_("Authority date"),
        description=_("authority_date_description"),
        required=False,
    )

    expired_authority_date = schema.Date(
        title=_("Expired authority date"),
        description=_("expired_authority_date_description"),
        required=False,
    )

    # Timestamping fieldset
    model.fieldset(
        "timestamp",
        fields=["timestamped_file"],
    )
    write_permission(timestamped_file="cmf.ManagePortal")
    timestamped_file = NamedBlobFile(title="Timestamped file", accept=("application/zip",), required=False)

    # Making sure timestamp file is accessible to anonymous.
    # By default it has a custom permission
    read_permission(timestamp="zope2.View")


@implementer(IPublication)
class Publication(Container, File):
    """ """

    security = ClassSecurityInfo()

    @security.protected(View)
    def Description(self):
        """Overrided to keep line breaks."""
        return self.description or ""

    def _get_institution(self):
        """ """
        return api.portal.get_navigation_root(self)

    def is_power_user(self):
        """ """
        institution = self._get_institution()
        return (
            not institution.publications_power_users
            or api.user.get_current().getId() in institution.publications_power_users
        )

    def is_timestamped(self):
        return ITimeStamper(self).is_timestamped()

    def may_back_to_private(self):
        """Only Manager may back to private except if
        current review_state is "planned"."""
        user = api.user.get_current()
        if api.content.get_state(self) == "planned":
            # Editor can't edit it directly, but can put it back to private to edit it.
            return user.has_role("Editor", object=self) or _checkPermission(ManagePortal, self)
        else:
            return _checkPermission(ManagePortal, self)

    def may_plan(self):
        """May plan if able to modify and
        a "publication date" (effectiveDate) is defined."""
        return (
            _checkPermission(ModifyPortalContent, self)
            and self.effective_date is not None
            and self.effective_date > DateTime()
        )

    def may_publish(self):
        """May publish if able to modify."""
        return _checkPermission(ModifyPortalContent, self)


@indexer(IPublication)
def get_decision_date(obj):
    return obj.decision_date


@indexer(IPublication)
def get_effective_date(obj):
    """As elements are sorted in the faceted on effective date, if no date, it
    it not returned so set a date of 01/01/1950 for publications without an
    effective date."""
    return obj.effective_date or EMPTY_DATETIME


@indexer(IPublication)
def get_effective_year(obj):
    return str(obj.effective_date.year()) if obj.effective_date else None


@indexer(IPublication)
def get_pretty_category(obj):
    global_categories = api.portal.get_registry_record(name="plonemeeting.portal.core.global_categories")
    return global_categories.copy().get(obj.category, [])


@indexer(IPublication)
def get_pretty_document_type(obj):
    document_types = api.portal.get_registry_record(name="plonemeeting.portal.core.document_types")
    return document_types.copy().get(obj.document_type, [])


@indexer(IPublication)
def get_annexes_infos(obj):
    index = []
    request = getRequest()
    if request is None:
        raise AttributeError
    for annex in object_values(object, "File"):
        utils_view = getMultiAdapter((annex, request), name="file_view")
        # Unfortunately, we can't store dicts
        index.append((annex.title, annex.absolute_url(), utils_view.getMimeTypeIcon(annex.file)))
    return index


@indexer(IPublication)
def has_annexes(obj):
    return bool(object_values(obj, "File"))
