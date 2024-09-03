# -*- coding: utf-8 -*-
"""Init and utils."""
from plonemeeting.portal.core import patches  # NOQA
from zope.i18nmessageid import MessageFactory

import logging


logger = logging.getLogger("plonemeeting.portal.core")


assert patches  # workaround for pyflakes issue #13, NOQA

_ = MessageFactory("plonemeeting.portal.core")
plone_ = MessageFactory("plone")
