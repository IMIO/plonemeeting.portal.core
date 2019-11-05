# -*- coding: utf-8 -*-
from plone.dexterity.content import Item
from plone.namedfile import field as namedfile
from plone.supermodel import model
from zope.interface import implementer


from plonemeeting.portal.core import _


class IAnnex(model.Schema):
    """ Marker interface and Dexterity Python Schema for Annex
    """

    file = namedfile.NamedBlobFile(title=_(u"File"), required=True)


@implementer(IAnnex)
class Annex(Item):
    """
    """
