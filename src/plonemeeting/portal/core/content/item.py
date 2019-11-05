# -*- coding: utf-8 -*-

from Products.CMFPlone import PloneMessageFactory as plone_
from plone.app.textfield import RichText
from plone.dexterity.content import Container
from plone.supermodel import model
from zope import schema
from zope.interface import implementer

from plonemeeting.portal.core import _
from plonemeeting.portal.core import vocabulary


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

    decision = RichText(title=_(u"Decision"), required=False)

    point_type = schema.Choice(
        title=_(u"Point type"), vocabulary=vocabulary.item_point_type, required=True
    )

    category = schema.Choice(
        title=_(u"Category/Matter"), vocabulary=vocabulary.item_category, required=True
    )

    extra_info = RichText(title=_(u"Extra info"), required=False)


@implementer(IItem)
class Item(Container):
    """
    """
