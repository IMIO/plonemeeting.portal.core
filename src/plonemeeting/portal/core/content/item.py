# -*- coding: utf-8 -*-
# from plone.app.textfield import RichText
# from plone.autoform import directives
from plone.dexterity.content import Container
from plone.namedfile import field as namedfile
# from plone.namedfile import field as namedfile
from plone.supermodel import model
# from plone.supermodel.directives import fieldset
# from z3c.form.browser.radio import RadioFieldWidget
# from zope import schema
from zope.interface import implementer
from zope import schema

from plonemeeting.portal.core import _
from plonemeeting.portal.core import vocabulary


class IItem(model.Schema):
    """ Marker interface and Dexterity Python Schema for Item
    """

    point_number = schema.Text(
        title=_(u'Point number'),
        required=True
    )

    uid = schema.Text(
        title=_(u'PM UID'),
        required=True
    )

    text = schema.RichText(
        title=_(u'Text'),
        required=False
    )

    # directives.widget(level=RadioFieldWidget)
    point_type = schema.Choice(
        title=_(u'Point type'),
        vocabulary=vocabulary.item_point_type,
        required=True
    )

    category = schema.Choice(
        title=_(u'Category/Matter'),
        vocabulary=vocabulary.item_category,
        required=True
    )

    annexe = namedfile.NamedBlobFile(
        title=_(u"annexe", default=u"File"),
        required=True,
    )

    description = schema.RichText(
        title=_(u'Text'),
        required=False
    )


@implementer(IItem)
class Item(Container):
    """
    """
