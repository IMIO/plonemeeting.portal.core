# -*- coding: utf-8 -*-

from Products.CMFPlone.interfaces.constrains import ISelectableConstrainTypes

from plone import api


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
