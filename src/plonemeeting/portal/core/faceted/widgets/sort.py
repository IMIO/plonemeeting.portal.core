# -*- coding: utf-8 -*-

from eea.facetednavigation.widgets import ViewPageTemplateFile
from eea.facetednavigation.widgets.interfaces import DefaultSchemata as DS
from eea.facetednavigation.widgets.interfaces import ISchema
from eea.facetednavigation.widgets.widget import Widget
from z3c.form import field

from plonemeeting.portal.core import _


class IItemsSortSchema(ISchema):
    """
    """


class DefaultSchemata(DS):
    """ Schemata default
    """

    fields = field.Fields(ISchema).select(u"title")


class ItemsSortWidget(Widget):
    """ Sort items with custom (multiple) sort orders
    """

    widget_type = "items_sort"
    widget_label = _("Items sort order")
    groups = (DefaultSchemata,)

    index = ViewPageTemplateFile("sort.pt")

    def query(self, form):
        """ Sort items by meeting date (desc) and by item number (asc)
        """
        # XXX avoid double sort_on when we selected a meeting
        # this is not necessary and it some case, produce weird results
        if 'seance' in form:
            query = {
                "sort_on": ["item_number"],
                "sort_order": ["ascending"],
            }
        else:
            query = {
                "sort_on": ["linkedMeetingDate", "item_number"],
                "sort_order": ["descending", "ascending"],
            }
        return query
