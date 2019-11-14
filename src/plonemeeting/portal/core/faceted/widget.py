# -*- coding: utf-8 -*-

from eea.facetednavigation.widgets import ViewPageTemplateFile
from eea.facetednavigation.widgets.interfaces import DefaultSchemata as DS
from eea.facetednavigation.widgets.interfaces import ISchema
from eea.facetednavigation.widgets.widget import Widget
from z3c.form import field

from plonemeeting.portal.core import _


class DefaultSchemata(DS):
    """ Schemata default
    """

    fields = field.Fields(ISchema).select(u"title")


class RelativePathWidget(Widget):
    """ Filter on objects from current folder
    """

    widget_type = "relative_path"
    widget_label = _("Relative path")
    groups = (DefaultSchemata,)

    index = ViewPageTemplateFile("widget.pt")

    def query(self, form):
        """ Returns only objects from current folder
        """
        current_path = "/".join(self.context.getPhysicalPath())
        query = {"path": {"query": current_path}}
        return query
