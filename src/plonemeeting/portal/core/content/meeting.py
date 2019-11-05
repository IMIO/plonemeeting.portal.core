# -*- coding: utf-8 -*-
# from plone.app.textfield import RichText
# from plone.autoform import directives
from plone.dexterity.content import Container
# from plone.namedfile import field as namedfile
from plone.supermodel import model
# from plone.supermodel.directives import fieldset
# from z3c.form.browser.radio import RadioFieldWidget
from zope import schema
from zope.interface import implementer

from plonemeeting.portal.core import _


class IMeeting(model.Schema):
    """ Marker interface and Dexterity Python Schema for Meeting
    """
    datetime = schema.Datetime(
        title=_(u'MeetingDatetime'),
        required=True,
        readonly=True,
    )

    attentees = schema.Text(
        title=_(u'Assembly'),
        required=True,
    )


@implementer(IMeeting)
class Meeting(Container):
    """
    """
