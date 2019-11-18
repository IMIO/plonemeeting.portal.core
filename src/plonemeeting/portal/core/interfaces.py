# -*- coding: utf-8 -*-

from eea.facetednavigation.interfaces import IFacetedNavigable
from zope.publisher.interfaces.browser import IDefaultBrowserLayer


class IPlonemeetingPortalCoreLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


class IMeetingsFolder(IFacetedNavigable):
    """Marker interface for Meetings folder"""


class IItemsFolder(IFacetedNavigable):
    """Marker interface for Items folder"""
