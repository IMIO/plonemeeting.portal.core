# -*- coding: utf-8 -*-
from plone.app.z3cform.utils import call_callables
from plone.app.z3cform.widgets.richtext import get_tinymce_options, RichTextWidget
from plonemeeting.portal.core import logger
from Products.CMFPlone.resources import utils
from Products.CMFPlone.resources.utils import get_resource
from Products.PortalTransforms.transforms import safe_html
from Products.PortalTransforms.transforms.safe_html import CSS_COMMENT
from Products.PortalTransforms.transforms.safe_html import decode_htmlentities

import logging


original_hasScript = safe_html.hasScript

def hasScript(s):
    """Override to keep data:image elements, turned 'data:' to 'data:text'
    """
    s = decode_htmlentities(s)
    s = s.replace('\x00', '')
    s = CSS_COMMENT.sub('', s)
    s = ''.join(s.split()).lower()
    for t in ('script:', 'expression:', 'expression(', 'data:text'):
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


def get_pattern_options(self):
    pattern_options = get_tinymce_options(
        self.wrapped_context(),
        self.field,
        self.request,
    )
    directive_pattern_options = call_callables(self.pattern_options, self.context)
    return {
        **pattern_options,
        **directive_pattern_options,
        "relatedItems": {
            **pattern_options.get("relatedItems", {}),
            **directive_pattern_options.get("relatedItems", {}),
        },
    }

RichTextWidget._original_get_pattern_options = RichTextWidget.get_pattern_options
RichTextWidget.get_pattern_options = get_pattern_options
