# -*- coding: utf-8 -*-
import logging

from Products.CMFPlone.resources import utils
from Products.CMFPlone.resources.utils import get_resource
from Products.PortalTransforms.transforms import safe_html
from Products.PortalTransforms.transforms.safe_html import CSS_COMMENT
from Products.PortalTransforms.transforms.safe_html import decode_htmlentities
from plone.app.z3cform.widgets import contentbrowser
from plone.base.navigationroot import get_navigation_root_object
from plone.base.utils import get_top_site_from_url
from plonemeeting.portal.core import logger
from zope.globalrequest import getRequest

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


original_get_resource = get_resource


def get_resource(*args, **kwargs):
    """Override to disable useless verbose logger when getting a resource."""
    logger = logging.getLogger("Products.CMFPlone.resources.utils")
    logger.disabled = True
    try:
        return original_get_resource(*args, **kwargs)
    finally:
        logger.disabled = False


utils.get_resource = get_resource
logger.info("Patching Products.CMFPlone.resources.utils (get_resource)")

contentbrowser._original_get_contentbrowser_options = contentbrowser.get_contentbrowser_options


def get_contentbrowser_options(*args, **kwargs):
    """If we are in an institution, we need to set the rootPath to the institution"""
    res = contentbrowser._original_get_contentbrowser_options(*args, **kwargs)
    context = args[0] if args else kwargs.get("context")
    request = getRequest()
    site = get_top_site_from_url(context, request)
    nav_root = get_navigation_root_object(context, site)
    utils_view = context.restrictedTraverse("@@utils_view")
    if utils_view.is_in_institution():
        res["rootPath"] = "/".join(nav_root.getPhysicalPath()) if nav_root else "/"
    return res


contentbrowser.get_contentbrowser_options = get_contentbrowser_options
