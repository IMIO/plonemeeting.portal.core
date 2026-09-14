# -*- coding: utf-8 -*-
"""Extraction shim: restate the ZCML msgids where a catalog rebuild can see them.

``i18ndude`` extracts from Python and page templates, never from ZCML.  The
subject and preheader of every mail live in ``emails.zcml``, with the
``emailkit:template`` registration that translates them per recipient, so
without this module a rebuilt ``.pot`` would silently drop them and every
recipient would get the bare msgid as a subject line.

Nothing imports this module: it exists to be read by the extractor.  Keep it in
step with ``emails.zcml`` by hand -- the default text has to match, or the two
disagree about what an untranslated language shows.
"""
from plonemeeting.portal.core import _


_(
    "email_subject_sso_migrated",
    default="Your Délibérations.be account now uses Wallonie Connect",
)
_(
    "email_preheader_sso_migrated",
    default="Log in from now on with Wallonie Connect, using your email address.",
)
