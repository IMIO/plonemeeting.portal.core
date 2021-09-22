# -*- coding: utf-8 -*-

from plonemeeting.portal.core import logger
from Products.PortalTransforms.transforms import safe_html
from Products.PortalTransforms.transforms.safe_html import CSS_COMMENT
from Products.PortalTransforms.transforms.safe_html import decode_htmlentities


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
