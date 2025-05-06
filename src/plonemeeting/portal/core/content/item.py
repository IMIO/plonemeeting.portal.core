# -*- coding: utf-8 -*-
from copy import deepcopy
from imio.helpers.content import object_values
from plone import api
from plone.app.dexterity.textindexer import searchable
from plone.app.textfield import RichText
from plone.app.textfield.interfaces import ITransformer
from plone.dexterity.content import Container
from plone.indexer.decorator import indexer
from plone.supermodel import model
from plonemeeting.portal.core import _
from Products.CMFPlone import PloneMessageFactory as plone_
from zope import schema
from zope.component import getMultiAdapter
from zope.globalrequest import getRequest
from zope.interface import implementer


class IItem(model.Schema):
    """ Marker interface and Dexterity Python Schema for Item
    """

    searchable("formatted_title")
    formatted_title = RichText(title=plone_(u"Title"), required=False, readonly=True)

    number = schema.TextLine(title=_(u"Item number"), required=True, readonly=True)

    sortable_number = schema.Int(
        title=_(u"Sortable Item number"), required=True, readonly=True
    )

    plonemeeting_uid = schema.TextLine(
        title=_(u"UID Plonemeeting"), required=True, readonly=True
    )

    representatives_in_charge = schema.List(
        value_type=schema.Choice(
            vocabulary="plonemeeting.portal.vocabularies.representatives"
        ),
        title=_(u"Representative group in charge"),
        required=False,
        readonly=True,
    )

    long_representatives_in_charge = schema.List(
        value_type=schema.Choice(
            vocabulary="plonemeeting.portal.vocabularies.long_representatives"
        ),
        title=_(u"Representative group in charge"),
        required=False,
        readonly=True,
    )

    additional_data = RichText(
        title=_(u"Additional data"), required=False, readonly=True
    )

    searchable("decision")
    decision = RichText(title=_(u"Decision"), required=False, readonly=True)

    category = schema.Choice(
        vocabulary="plonemeeting.portal.vocabularies.global_categories",
        title=_(u"Category"),
        required=False,
        readonly=True,
    )

    custom_info = RichText(title=_(u"Custom info"), required=False)

    plonemeeting_last_modified = schema.Datetime(
        title=_(u"Last modification in iA.Delib"), required=True, readonly=True
    )


@implementer(IItem)
class Item(Container):
    """
    """

    def get_title(self):
        if not hasattr(self, "_formatted_title"):
            pass
        return self._formatted_title

    def set_title(self, value):
        self._formatted_title = value
        transformer = ITransformer(self)
        if value:
            _title = transformer(value, "text/plain").strip()
            self.title = _title
        else:
            self.title = None

    formatted_title = property(get_title, set_title)


@indexer(IItem)
def get_pretty_representatives(object):
    representative_keys = deepcopy(object.representatives_in_charge)

    if not representative_keys:
        raise AttributeError
    res = []
    institution = api.portal.get_navigation_root(object)
    mapping = institution.representatives_mappings
    representatives_mapping = {infos["representative_key"]: infos["representative_value"]
                               for infos in mapping}
    for representative_key in representative_keys:
        value = representatives_mapping.get(representative_key)
        if value and value not in res:
            res.append(value)

    if res:
        return ", ".join(res)
    raise AttributeError


@indexer(IItem)
def get_pretty_category(object):
    # use .copy() to make sure to return a copy of the record
    global_categories = api.portal.get_registry_record(
        name="plonemeeting.portal.core.global_categories"
    )
    if not global_categories or object.category not in global_categories:
        raise AttributeError

    copy_of_categories = global_categories.copy()
    return copy_of_categories[object.category]


@indexer(IItem)
def get_title_from_meeting(object):
    meeting = object.aq_parent
    return meeting.title


@indexer(IItem)
def get_UID_from_meeting(object):
    meeting = object.aq_parent
    return meeting.UID()


@indexer(IItem)
def get_datetime_from_meeting(object):
    meeting = object.aq_parent
    return meeting.date_time


@indexer(IItem)
def get_review_state_from_meeting(object):
    meeting = object.aq_parent
    return api.content.get_state(meeting)


@indexer(IItem)
def get_year_from_meeting(object):
    meeting = object.aq_parent
    date_time = meeting.date_time
    if date_time:
        # date_time is a python datetime
        return str(date_time.year)


@indexer(IItem)
def get_annexes_infos(object):
    index = []
    request = getRequest()
    if request is None:
        raise AttributeError
    for annex in object_values(object, "File"):
        utils_view = getMultiAdapter((annex, request), name="file_view")
        # Unfortunately, we can't store dicts
        index.append((annex.title, annex.absolute_url(), utils_view.getMimeTypeIcon(annex.file)))
    return index


@indexer(IItem)
def has_annexes(object):
    return bool(object_values(object, "File"))


@indexer(IItem)
def get_formatted_title_output(object):
    return object.formatted_title.output
