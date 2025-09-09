# -*- coding: utf-8 -*-
from plone.app.contenttypes.behaviors.tableofcontents import ITableOfContents
from plone.app.z3cform.widgets import contentbrowser
from plone.base.navigationroot import get_navigation_root_object
from plone.base.utils import get_top_site_from_url
from plone.supermodel.interfaces import FIELDSETS_KEY
from plonemeeting.portal.core import logger
from plonemeeting.portal.core.interfaces import IPlonemeetingPortalCoreLayer
from Products.CMFPlone.resources import utils
from Products.CMFPlone.resources.utils import get_resource
from Products.PortalTransforms.transforms import safe_html
from Products.PortalTransforms.transforms.safe_html import CSS_COMMENT
from Products.PortalTransforms.transforms.safe_html import decode_htmlentities
from z3c.form.interfaces import IForm
from zope.globalrequest import getRequest

import logging


original_hasScript = safe_html.hasScript


def hasScript(s):
    """Override to keep data:image elements, turned 'data:' to 'data:text'"""
    s = decode_htmlentities(s)
    s = s.replace("\x00", "")
    s = CSS_COMMENT.sub("", s)
    s = "".join(s.split()).lower()
    for t in ("script:", "expression:", "expression(", "data:text"):
        if t in s:
            return True
    return False


safe_html.hasScript = hasScript
logger.info("Patching Products.PortalTransforms.transforms.safe_html (hasScript)")


contentbrowser._original_get_contentbrowser_options = contentbrowser.get_contentbrowser_options


def get_contentbrowser_options(*args, **kwargs):  # pragma: no cover
    """If we are in an institution, we need to set the rootPath to the institution"""
    res = contentbrowser._original_get_contentbrowser_options(*args, **kwargs)
    context = args[0] if args else kwargs.get("context")
    if IForm.providedBy(context):  # Sometimes context is a form
        context = context.context
    if not IPlonemeetingPortalCoreLayer.implementedBy(context):
        # Don't break if plonemeeting.portal.core is not installed
        return res
    request = getRequest()
    site = get_top_site_from_url(context, request)
    nav_root = get_navigation_root_object(context, site)
    utils_view = context.unrestrictedTraverse("@@utils_view")
    if utils_view.is_in_institution():
        res["rootPath"] = "/".join(nav_root.getPhysicalPath()) if nav_root else "/"
        res["rootUrl"] = "/".join(nav_root.getPhysicalPath()) if nav_root else "/"
    return res


contentbrowser.get_contentbrowser_options = get_contentbrowser_options
logger.info("Patching plone.app.z3cform.widgets import contentbrowser (get_contentbrowser_options)")


def remove_behavior_field_fieldset(interface, fieldname):
    try:
        fieldsets = interface.getTaggedValue(FIELDSETS_KEY)
    except KeyError:
        fieldsets = []
        interface.setTaggedValue(FIELDSETS_KEY, fieldsets)

    for fs in fieldsets:
        if fieldname in fs.fields:
            fs.fields.remove(fieldname)
            break


remove_behavior_field_fieldset(ITableOfContents, "table_of_contents")
logger.info(
    "Patching plone.app.contenttypes.behaviors.tableofcontents to move ITableOfContents.table_of_contents field"
)
