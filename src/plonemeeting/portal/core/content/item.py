# -*- coding: utf-8 -*-

from Products.CMFPlone import PloneMessageFactory as plone_
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

    point_number = schema.TextLine(title=_(u"Point number"), required=True)

    uid = schema.TextLine(title=_(u"UID Plonemeeting"), required=True)

    representative_group_in_charge_key = schema.TextLine(
        title=_(u"Reprensentative group in charge key"), required=False
    )

    decision = RichText(title=_(u"Decision"), required=False)

    item_type = schema.Choice(
        title=_(u"Item type"),
        vocabulary="plonemeeting.portal.vocabularies.item_types",
        required=True,
    )

    category = schema.Choice(
        title=_(u"Category/Matter"),
        vocabulary="plonemeeting.portal.vocabularies.categories",
        required=True,
    )

    extra_info = RichText(title=_(u"Extra info"), required=False)


@implementer(IItem)
class Item(Container):
    """
    """


@indexer(IItem)
def get_datetime_from_meeting(object):
    meeting = object.aq_parent
    return meeting.meeting_datetime


@indexer(IItem)
def get_year_from_meeting(object):
    meeting = object.aq_parent
    meeting_datetime = meeting.meeting_datetime
    if meeting_datetime:
        return meeting_datetime.year
