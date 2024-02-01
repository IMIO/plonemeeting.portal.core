# -*- coding: utf-8 -*-

from eea.facetednavigation.interfaces import IFacetedNavigable
from zope.interface import Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer


class IPlonemeetingPortalCoreLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


class IMeetingsFolder(IFacetedNavigable):
    """Marker interface for Meetings folder"""


class IItemsFolder(IFacetedNavigable):
    """Kept while migrating to 1003, to be removed after"""


class IInstitutionSerializeToJson(Interface):
    """Adapter to serialize an Institution object into a JSON object."""


class IUtilsView(Interface):
    """"""
    def is_institution(self):
        """See IUtilsView"""
        return True
