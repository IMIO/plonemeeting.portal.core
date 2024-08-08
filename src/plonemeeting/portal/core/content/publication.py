from imio.helpers import EMPTY_DATETIME
from imio.helpers.content import object_values
from plone import api
from plone.app.contenttypes.content import File
from plone.app.contenttypes.interfaces import IFile
from plone.app.textfield import RichText
from plone.dexterity.content import Container
from plone.indexer.decorator import indexer
from plone.namedfile.field import NamedBlobFile
from plone.supermodel import model
from plonemeeting.portal.core import _
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

    authority_date = schema.Date(
        title=_(u"Authority date"),
        required=False,
    )

    consultation_text = RichText(
        title=_(u"Hour and place of consultation"),
        required=False
    )

    model.primary('file')
    file = NamedBlobFile(
        title="File",
        accept=("application/pdf", ),
        required=False)


@implementer(IPublication)
class Publication(Container, File):
    """
    """


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
    effective = obj.effective
    if effective:
        return str(effective.year)


@indexer(IPublication)
def get_document_type(obj):
    return obj.document_type


@indexer(IPublication)
def get_pretty_category(obj):
    global_categories = api.portal.get_registry_record(
        name="plonemeeting.portal.core.global_categories"
    )
    return global_categories.copy()[obj.category]


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
    files = obj.listFolderContents(contentFilter={"portal_type": "File"})
    for annex in files:
        utils_view = getMultiAdapter((annex, request), name="file_view")
        # Unfortunately, we can't store dicts
        index.append((annex.title, annex.absolute_url(), utils_view.getMimeTypeIcon(annex.file)))
    return index


@indexer(IPublication)
def has_annexes(obj):
    return bool(object_values(obj, "File"))
