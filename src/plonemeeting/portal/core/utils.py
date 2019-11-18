# -*- coding: utf-8 -*-

from Products.CMFPlone.interfaces.constrains import ISelectableConstrainTypes
from plone import api
from plone.portlets.interfaces import IPortletAssignmentMapping
from plone.portlets.interfaces import IPortletManager
from zope.component import getMultiAdapter
from zope.component import getUtility

from plonemeeting.portal.core.config import CONTENTS_TO_CLEAN


def create_faceted_folder(container, title, id=None):
    if id:
        folder = api.content.create(
            type="Folder", title=title, container=container, id=id
        )
    else:
        folder = api.content.create(type="Folder", title=title, container=container)
    api.content.transition(folder, to_state="published")
    subtyper = folder.restrictedTraverse("@@faceted_subtyper")
    subtyper.enable()
    set_constrain_types(folder, [])
    return folder


def set_constrain_types(obj, list_contraint):
    behavior = ISelectableConstrainTypes(obj)
    behavior.setConstrainTypesMode(1)
    behavior.setImmediatelyAddableTypes(list_contraint)
    behavior.setLocallyAllowedTypes(list_contraint)


def cleanup_contents():
    portal = api.portal.get()
    for content_id in CONTENTS_TO_CLEAN:
        content = getattr(portal, content_id, None)
        if content:
            api.content.delete(content)


def remove_left_portlets():
    remove_portlets("plone.leftcolumn")


def remove_right_portlets():
    remove_portlets("plone.rightcolumn")


def remove_portlets(column):
    portal = api.portal.get()
    manager = getUtility(IPortletManager, name=column, context=portal)
    assignments = getMultiAdapter((portal, manager), IPortletAssignmentMapping)
    for portlet in assignments:
        del assignments[portlet]
