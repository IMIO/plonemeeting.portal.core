# -*- coding: utf-8 -*-
from plone.dexterity.content import Item
from plone.namedfile import field as namedfile
from plone.supermodel import model
from zope.interface import implementer
from zope import schema


from plonemeeting.portal.core import _


class IAnnex(model.Schema):
    """ Marker interface and Dexterity Python Schema for Annex
    """
    title = schema.TextLine(
        title=_(u"label_title", default=u"Title"),
        required=True,
        # readonly=True
    )

    file = namedfile.NamedBlobFile(
        title=_(u"label_file", default=u"File"),
        required=True,
        # readonly=True
    )


@implementer(IAnnex)
class Annex(Item):
    """
    """
