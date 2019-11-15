# -*- coding: utf-8 -*-

from Products.CMFPlone import PloneMessageFactory as plone_
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

    title = schema.TextLine(
        title=plone_(u"Title"),
        required=True,
        # readonly=True
    )

    number = schema.TextLine(title=_(u"Item number"), required=True)

    uid = schema.TextLine(title=_(u"UID Plonemeeting"), required=True)

    representative_group_in_charge = schema.Choice(
        title=_(u"Representative group in charge"),
        vocabulary="plonemeeting.portal.vocabularies.representatives",
        required=False,
    )

    deliberation = RichText(title=_(u"Deliberation"), required=False)

    item_type = schema.Choice(
        title=_(u"Item type"),
        vocabulary="plonemeeting.portal.vocabularies.item_types",
        required=True,
    )

    category = schema.Choice(
        title=_(u"Category"),
        vocabulary="plonemeeting.portal.vocabularies.global_categories",
        required=True,
    )

    extra_info = RichText(title=_(u"Extra info"), required=False)


@implementer(IItem)
class Item(Container):
    """
    """


@indexer(IItem)
def get_item_number(object):
    return object.number


@indexer(IItem)
def get_pretty_representative(object):
    representative_key = object.representative_group_in_charge
    if not representative_key:
        raise AttributeError
    institution = api.portal.get_navigation_root(object)
    mapping = institution.representatives_mappings
    for infos in mapping:
        if infos["representative_key"] == representative_key:
            return infos["representative_value"]
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
        return date_time.year
