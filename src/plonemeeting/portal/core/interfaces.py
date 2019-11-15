# -*- coding: utf-8 -*-

from zope.interface import Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer


class IPlonemeetingPortalCoreLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


class IMeetingsFolder(Interface):
    """Marker interface for Meetings folder"""
