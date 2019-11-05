# -*- coding: utf-8 -*-

from Products.CMFPlone import PloneMessageFactory as plone_
from plone.dexterity.content import Item
from plone.namedfile import field as namedfile
from plone.supermodel import model
from zope import schema
from zope.interface import implementer

from plonemeeting.portal.core import _


class IAnnex(model.Schema):
    """ Marker interface and Dexterity Python Schema for Annex
    """

    title = schema.TextLine(
        title=plone_(u"Title"),
        required=True,
        # readonly=True
    )

    annex_file = namedfile.NamedBlobFile(
        title=_(u"Annex"),
        required=True,
        # readonly=True
    )


@implementer(IAnnex)
class Annex(Item):
    """
    """
