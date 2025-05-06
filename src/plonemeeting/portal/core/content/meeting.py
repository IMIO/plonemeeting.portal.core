# -*- coding: utf-8 -*-
from plone.app.textfield import RichText
from plone.autoform import directives
from plone.dexterity.content import Container
from plone.folder.interfaces import IOrdering
from plone.folder.unordered import UnorderedOrdering
from plone.supermodel import model
from plonemeeting.portal.core import _
from plonemeeting.portal.core.content.item import IItem
from Products.CMFCore.permissions import ManagePortal
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as plone_
from zope import schema
from zope.component import adapter
from zope.interface import implementer


class IMeeting(model.Schema):
    """Marker interface and Dexterity Python Schema for Meeting"""

    title = schema.TextLine(title=plone_("Title"), required=True, readonly=True)

    plonemeeting_uid = schema.TextLine(
        title=_("UID Plonemeeting"),
        required=True,
        readonly=True,
    )

    directives.write_permission(date_time=ManagePortal)
    date_time = schema.Datetime(
        title=plone_("Date"),
        required=True,
        readonly=False,
    )

    custom_info = RichText(title=_("Custom info"), required=False)

    plonemeeting_last_modified = schema.Datetime(title=_("Last modification in iA.Delib"), required=True, readonly=True)


@implementer(IMeeting)
class Meeting(Container):
    """ """

    def get_items(self, objects=True):
        portal_catalog = getToolByName(self, "portal_catalog")
        meeting_path = "/".join(self.getPhysicalPath())
        brains = portal_catalog(
            object_provides=IItem.__identifier__, path={"query": meeting_path, "depth": 1}, sort_on="sortable_number"
        )
        if objects:
            return [brain.getObject() for brain in brains]
        return brains


@implementer(IOrdering)
@adapter(IMeeting)
class ItemNumberOrdering(UnorderedOrdering):
    """This implementation provides ordering based on the item number of the contained items."""

    def idsInOrder(self):
        return [i.id for i in self.context.get_items(objects=False)]
