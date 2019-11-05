# -*- coding: utf-8 -*-
# from plone.app.textfield import RichText
# from plone.autoform import directives
from plone.app.textfield import RichText
from plone.dexterity.content import Container

# from plone.namedfile import field as namedfile
from plone.supermodel import model

# from plone.supermodel.directives import fieldset
# from z3c.form.browser.radio import RadioFieldWidget
from zope import schema
from zope.interface import implementer

from plonemeeting.portal.core import _
from Products.CMFPlone import PloneMessageFactory as plone_


class IMeeting(model.Schema):
    """ Marker interface and Dexterity Python Schema for Meeting
    """

    title = schema.TextLine(title=plone_(u"Title"), required=True, readonly=True)

    meeting_datetime = schema.Datetime(
        title=plone_(u"Date"), required=True, readonly=True,
    )

    attentees = schema.Text(title=_(u"Assembly"), required=True,)

    extra_info = RichText(title=_(u"Extra Info"))


@implementer(IMeeting)
class Meeting(Container):
    """
    """
