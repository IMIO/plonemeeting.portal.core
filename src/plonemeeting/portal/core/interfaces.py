# -*- coding: utf-8 -*-

from eea.facetednavigation.interfaces import IFacetedNavigable
from plone.app.z3cform.interfaces import IPloneFormLayer
from plone.locking.interfaces import ITTWLockable
from zope.interface import Interface


class IPlonemeetingPortalCoreLayer(IPloneFormLayer):
    """Marker interface that defines a browser layer."""


class IPlonemeetingPortalConfigFolder(Interface):
    """Marker interface for Plonemeeting config folder"""


class IMeetingsFolder(IFacetedNavigable, ITTWLockable):
    """Marker interface for Meetings folder

    ITTWLockable makes ``ILockable(decisions_folder)`` resolvable through
    plone.locking's own adapter, which the meeting synchronization guard
    relies on to serialize concurrent imports.
    """


class IPublicationsFolder(IFacetedNavigable):
    """Marker interface for Publications folder"""


class IInstitutionSettingsView(Interface):
    """Marker interface for Institution settings view"""


class IUtilsView(Interface):
    """"""

    def is_institution(self):
        pass

    def is_in_institution(self):
        pass

    def get_settings_url(self):
        pass

    def show_settings_tab(self):
        pass

    def is_meeting(self):
        pass
