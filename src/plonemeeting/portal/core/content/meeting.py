# -*- coding: utf-8 -*-

from Products.CMFCore.permissions import ManagePortal
from Products.CMFPlone import PloneMessageFactory as plone_
from plone.app.textfield import RichText
from plone.autoform import directives as form
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
        readonly=True
    )

    plonemeeting_uid = schema.TextLine(
        title=_(u"UID Plonemeeting"),
        required=True,
        readonly=True,
    )

    form.write_permission(date_time=ManagePortal)
    date_time = schema.Datetime(
        title=plone_(u"Date"),
        required=True,
        readonly=False,
    )

    custom_info = RichText(title=_(u"Custom info"), required=False)

    plonemeeting_last_modified = schema.Datetime(
        title=_(u"Last modification in ia.Delib"), required=True, readonly=True
    )


@implementer(IMeeting)
class Meeting(Container):
    """
    """
