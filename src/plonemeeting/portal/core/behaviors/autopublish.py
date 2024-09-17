# -*- coding: utf-8 -*-
from collective.autopublishing import MyMessageFactory as _
from collective.autopublishing.behavior import IAutoPublishing
from plone.autoform.directives import read_permission
from plone.autoform.directives import write_permission
from plone.autoform.interfaces import IFormFieldProvider
from zope import schema
from zope.interface import provider


@provider(IFormFieldProvider)
class IPMAutoPublishing(IAutoPublishing):
    """Override to restrict to Manager and to default to True."""

    read_permission(enableAutopublishing="cmf.ManagePortal")
    write_permission(enableAutopublishing="cmf.ManagePortal")

    enableAutopublishing = schema.Bool(
        title=_("enableAutopublishing", default="Enable autopublishing?"),
        required=False,
        default=True,
    )
