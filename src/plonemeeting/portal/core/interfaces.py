# -*- coding: utf-8 -*-

from eea.facetednavigation.interfaces import IFacetedNavigable
from plone.app.z3cform.interfaces import IPloneFormLayer
from zope.interface import Interface


class IPlonemeetingPortalCoreLayer(IPloneFormLayer):
    """Marker interface that defines a browser layer."""


class IMeetingsFolder(IFacetedNavigable):
    """Marker interface for Meetings folder"""


class IPublicationsFolder(IFacetedNavigable):
    """Marker interface for Publications folder"""


class IUtilsView(Interface):
    """"""
    def is_institution(self):
        """See IUtilsView"""
        return True

    def is_meeting(self):
        """See IUtilsView"""
        return True
