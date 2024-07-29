# -*- coding: utf-8 -*-

from copy import deepcopy
from imio.helpers.content import object_values
from plone import api
from plone.app.dexterity.textindexer import directives
from plone.app.textfield import RichText
from plone.dexterity.content import Container
from plone.indexer.decorator import indexer
from plone.supermodel import model
from plonemeeting.portal.core import _
from Products.CMFPlone import PloneMessageFactory as plone_
from zope import schema
from zope.component import getMultiAdapter
from zope.globalrequest import getRequest
from zope.interface import implementer


class IPublication(model.Schema):
    """ Marker interface and Dexterity Python Schema for Item
    """

    decision_date = schema.Datetime(
        title=_(u"Decision date"),
        required=False,
    )

    authority_date = schema.Datetime(
        title=_(u"Authority date"),
        required=False,
    )

    document_type = schema.List(
        value_type=schema.Choice(
            vocabulary="plonemeeting.portal.vocabularies.document_types"
        ),
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
        title=_(u"Legislative autority"),
        required=False,
    )

    consultation_text = RichText(
        title=_(u"Hour and place of consultation"),
        required=False
    )

    directives.searchable("text")
    text = RichText(
        title=_(u"Text"), required=False, readonly=True
    )


@implementer(IPublication)
class Publication(Container):
    """
    """


@indexer(IPublication)
def get_decision_date(obj):
    return obj.decision_date


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
