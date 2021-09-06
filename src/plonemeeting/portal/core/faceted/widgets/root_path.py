# -*- coding: utf-8 -*-

from eea.facetednavigation.widgets import ViewPageTemplateFile
from eea.facetednavigation.widgets.interfaces import DefaultSchemata as DS
from eea.facetednavigation.widgets.interfaces import ISchema
from eea.facetednavigation.widgets.widget import Widget
from plone import api
from plonemeeting.portal.core import _
from z3c.form import field


class INavigationRootPathSchema(ISchema):
    """
    """


class DefaultSchemata(DS):
    """ Schemata default
    """

    fields = field.Fields(ISchema).select(u"title")


class NavigationRootPathWidget(Widget):
    """ Filter on objects from current navigation root
    """

    widget_type = "navigation_root_path"
    widget_label = _("Navigation root path")
    groups = (DefaultSchemata,)

    index = ViewPageTemplateFile("root_path.pt")

    def query(self, form):
        """ Returns only objects from current navigation root
        """
        nav_root = api.portal.get_navigation_root(self.context)
        path = "/".join(nav_root.getPhysicalPath())
        query = {"path": {"query": path}}
        return query
