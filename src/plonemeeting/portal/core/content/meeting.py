# -*- coding: utf-8 -*-

from Products.CMFPlone import PloneMessageFactory as plone_
from plone.app.textfield import RichText
from plone.dexterity.content import Container
from plone.supermodel import model
from zope import schema
from zope.interface import implementer

from plonemeeting.portal.core import _


class IMeeting(model.Schema):
    """ Marker interface and Dexterity Python Schema for Meeting
    """

    title = schema.TextLine(
        title=plone_(u"Title"),
        required=True,
        # readonly=True
    )

    date_time = schema.Datetime(
        title=plone_(u"Date"),
        required=True,
        # readonly=True,
    )

    attendees = RichText(title=_(u"Assembly"), required=True)

    extra_info = RichText(title=_(u"Extra info"), required=False)


@implementer(IMeeting)
class Meeting(Container):
    """
    """
