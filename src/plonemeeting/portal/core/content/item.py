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
from zope.interface import implementer

from plonemeeting.portal.core import _


class IItem(model.Schema):
    """ Marker interface and Dexterity Python Schema for Item
    """

    dexteritytextindexer.searchable("title")

    title = schema.TextLine(
        title=plone_(u"Title"),
        required=True,
        readonly=True
    )

    formatted_title = RichText(title=plone_(u"Title"), required=False, readonly=True)

    number = schema.TextLine(title=_(u"Item number"), required=True)

    plonemeeting_uid = schema.TextLine(title=_(u"UID Plonemeeting"), required=True)

    representatives_in_charge = schema.List(
        value_type=schema.Choice(
            vocabulary="plonemeeting.portal.vocabularies.representatives",
        ),
        title=_(u"Representative group in charge"),
        required=False,
    )

    dexteritytextindexer.searchable("decision")
    decision = RichText(title=_(u"Decision"), required=False)

    category = schema.TextLine(title=_(u"Category"), required=True,)

    extra_info = RichText(title=_(u"Extra info"), required=False)

    plonemeeting_last_modified = schema.Datetime(
        title=_(u"Last modification in ia.Delib"), required=True, readonly=True
    )


@implementer(IItem)
class Item(Container):
    """
    """


@indexer(IItem)
def get_item_number(object):
    return object.number


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
