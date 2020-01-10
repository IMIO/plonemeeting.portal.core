# -*- coding: utf-8 -*-
from copy import deepcopy

from Products.CMFPlone import PloneMessageFactory as plone_
from collective import dexteritytextindexer
from plone import api
from plone.app.textfield import RichText
from plone.dexterity.content import Container
from plone.indexer.decorator import indexer
from plone.supermodel import model
from zope import schema
from zope.component import getMultiAdapter
from zope.globalrequest import getRequest
from zope.interface import implementer

from plonemeeting.portal.core import _
from plonemeeting.portal.core.utils import get_text_from_richtext


class IItem(model.Schema):
    """ Marker interface and Dexterity Python Schema for Item
    """

    dexteritytextindexer.searchable("base_title")
    base_title = schema.TextLine(title=plone_(u"Title"), required=True, readonly=True)

    dexteritytextindexer.searchable("formatted_title")
    formatted_title = RichText(title=plone_(u"Title"), required=False, readonly=True)

    number = schema.TextLine(title=_(u"Item number"), required=True, readonly=True)

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

    additional_data = RichText(
        title=_(u"Additional data"), required=False, readonly=True
    )

    dexteritytextindexer.searchable("decision")
    decision = RichText(title=_(u"Decision"), required=False, readonly=True)

    category = schema.Choice(
        vocabulary="plonemeeting.portal.vocabularies.global_categories",
        title=_(u"Category"),
        required=False,
        readonly=True,
    )

    custom_info = RichText(title=_(u"Custom info"), required=False)

    plonemeeting_last_modified = schema.Datetime(
        title=_(u"Last modification in ia.Delib"), required=True, readonly=True
    )


@implementer(IItem)
class Item(Container):
    """
    """

    def get_title(self):
        title = get_text_from_richtext(self.formatted_title)
        if not title:
            title = self.base_title
        return title

    def set_title(self, value):
        self.base_title = value

    title = property(get_title, set_title)


def _itemNumber_to_storedItemNumber(number):
    """XXX Taken from Products.PloneMeeting :
       This will transform a displayed item number to a sortable value (integer) :
       - 1 -> 100;
       - 2 --> 200;
       - 2.1 --> 201;
       - 2.9 --> 209;
       - 2.10 --> 210;
       - 2.22 --> 222;
       """
    if '.' in number:
        newInteger, newDecimal = number.split('.')
        newInteger = newInteger
        newDecimal = newDecimal.zfill(2)
        realMoveNumber = int('{0}{1}'.format(newInteger, newDecimal))
    else:
        realMoveNumber = int(number) * 100
    return realMoveNumber


@indexer(IItem)
def get_item_number(object):
    return _itemNumber_to_storedItemNumber(object.number)


@indexer(IItem)
def get_pretty_representatives(object):
    representative_keys = deepcopy(object.representatives_in_charge)

    if not representative_keys:
        raise AttributeError
    res = []
    institution = api.portal.get_navigation_root(object)
    mapping = institution.representatives_mappings
    for infos in mapping:
        representative_key = infos["representative_key"]
        if representative_key in representative_keys:
            representative_keys.remove(representative_key)
            res.append(infos["representative_value"])

    for missing_keys in representative_keys:
        res.append(missing_keys)

    if res:
        return ", ".join(res)
    raise AttributeError


@indexer(IItem)
def get_pretty_category(object):
    global_categories = api.portal.get_registry_record(
        name="plonemeeting.portal.core.global_categories"
    )
    if not global_categories or object.category not in global_categories:
        raise AttributeError

    return global_categories[object.category]


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
        return str(date_time.year)


@indexer(IItem)
def get_annexes_infos(object):
    index = []
    request = getRequest()
    if request is None:
        raise AttributeError
    files = object.listFolderContents(contentFilter={"portal_type": "File"})
    for annexe in files:
        utils_view = getMultiAdapter((annexe, request), name="file_view")
        icon = utils_view.get_mimetype_icon()
        # Unfortunately, we can't store dicts
        index.append((annexe.title, annexe.absolute_url(), icon))
    return index
