from DateTime import DateTime
from imio.helpers import EMPTY_DATETIME
from imio.helpers.content import object_values
from plone import api
from plone.app.contenttypes.content import File
from plone.app.contenttypes.interfaces import IFile
from plone.app.dexterity.textindexer import searchable
from plone.app.textfield import RichText
from plone.app.z3cform.widgets.richtext import RichTextFieldWidget
from plone.autoform.directives import widget
from plone.autoform.directives import write_permission
from plone.dexterity.content import Container
from plone.indexer.decorator import indexer
from plone.namedfile.field import NamedBlobFile
from plone.supermodel import model
from plonemeeting.portal.core import _
from Products.CMFCore.permissions import ManagePortal
from Products.CMFCore.permissions import ModifyPortalContent
from Products.CMFCore.utils import _checkPermission
from zope import schema
from zope.component import getMultiAdapter
from zope.globalrequest import getRequest
from zope.interface import implementer


class IPublication(model.Schema, IFile):
    """ Marker interface and Dexterity Python Schema for Publication
    """

    document_type = schema.Choice(
        vocabulary="plonemeeting.portal.vocabularies.document_types",
        title=_(u"Document type"),
        required=False,
    )

    category = schema.Choice(
        vocabulary="plonemeeting.portal.vocabularies.global_categories",
        title=_(u"Category"),
        required=False,
    )

    legislative_authority = schema.Choice(
        vocabulary="plonemeeting.portal.vocabularies.legislative_authorities",
        title=_(u"Legislative authority"),
        required=False,
    )

    decision_date = schema.Date(
        title=_(u"Decision date"),
        required=False,
    )

    entry_date = schema.Date(
        title=_(u"Entry date"),
        required=False,
    )

    consultation_text = RichText(
        title=_(u"Hour and place of consultation"),
        required=False
    )

    text = RichText(
        title=_("Text"),
        required=False,
    )
    widget("text", RichTextFieldWidget)
    searchable("text")

    model.primary('file')
    file = NamedBlobFile(
        title="File",
        accept=("application/pdf", ),
        required=False)

    write_permission(timestamped_file="cmf.ManagePortal")

    timestamped_file = NamedBlobFile(
        title="Timestamped file",
        accept=("application/zip", ),
        required=False)

    # Styling fieldset
    model.fieldset(
        "authority",
        label=_(u"Authority"),
        fields=[
            "subject_to_authority",
            "authority_date",
            "expired_authority_date",
        ],
    )
    subject_to_authority = schema.Bool(
        title=_(u"Subject to authority?"),
        required=False,
        default=True,
    )

    authority_date = schema.Date(
        title=_(u"Authority date"),
        description=_("authority_date_description"),
        required=False,
    )

    expired_authority_date = schema.Date(
        title=_(u"Expired authority date"),
        description=_("expired_authority_date_description"),
        required=False,
    )


@implementer(IPublication)
class Publication(Container, File):
    """
    """

    def _get_institution(self):
        """ """
        return api.portal.get_navigation_root(self)

    def is_power_user(self):
        """ """
        institution = self._get_institution()
        return not institution.publications_power_users or \
            api.user.get_current().getId() in institution.publications_power_users

    def may_back_to_private(self):
        """Only Manager may back to private except if
           current review_state is "planned"."""
        if api.content.get_state(self) == "planned":
            return _checkPermission(ModifyPortalContent, self)
        else:
            return _checkPermission(ManagePortal, self)

    def may_plan(self):
        """May plan if able to modify and
           a "publication date" (effectiveDate) is defined."""
        return _checkPermission(ModifyPortalContent, self) and \
            self.effective_date is not None and self.effective_date > DateTime()

    def may_publish(self):
        """May publish if able to modify and
           a "publication date" (effectiveDate) is NOT defined.
           When "unpublished" check that time stamp  was not modified."""
        return _checkPermission(ModifyPortalContent, self) and \
            (self.effective_date is None or
             (api.content.get_state(self) == "planned" and self.effective_date < DateTime()) or
             (api.content.get_state(self) == "unpublished" and
              self.is_power_user() and
              self.timestamp_still_valid()))

    def timestamp_still_valid(self):
        """Check if timestamp still corresponds to effective_date."""
        return True


@indexer(IPublication)
def get_decision_date(obj):
    return obj.decision_date


@indexer(IPublication)
def get_effective_date(obj):
    """As elements are sorted in the faceted on effective date, if no date, it
       it not returned so set a date of 01/01/1950 for publications without an
       effective date."""
    return obj.effective or EMPTY_DATETIME


@indexer(IPublication)
def get_effective_year(obj):
    effective = obj.effective_date
    if effective:
        # effective is a Zope DateTime
        return str(effective.year())


@indexer(IPublication)
def get_pretty_category(obj):
    global_categories = api.portal.get_registry_record(
        name="plonemeeting.portal.core.global_categories"
    )
    return global_categories.copy().get(obj.category, [])


@indexer(IPublication)
def get_pretty_document_type(obj):
    # use .copy() to make sure to return a copy of the record
    document_types = api.portal.get_registry_record(
        name="plonemeeting.portal.core.document_types"
    )
    return document_types.copy()[obj.document_type]


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
