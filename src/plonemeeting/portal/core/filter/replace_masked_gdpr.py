# -*- coding: utf-8 -*-
from plone.api.portal import get_navigation_root
from plone.api.portal import get_registry_record
from plone.outputfilters.interfaces import IFilter
from plonemeeting.portal.core.config import RGPD_MASKED_TEXT
from zope.interface import implements


class ReplaceMaskedGDPR(object):
    implements(IFilter)

    def __init__(self, context, request):
        self.context = context
        self.institution = get_navigation_root(self.context)
        self.request = request

    def is_enabled(self):
        return True

    def __call__(self, data):
        to_replace = get_registry_record("plonemeeting.portal.core.delib_masked_gdpr", RGPD_MASKED_TEXT)
        if hasattr(self.institution, "url_rgpd") and self.institution.url_rgpd:
            replace_by = self.institution.url_rgpd
        else:
            replace_by = get_registry_record("plonemeeting.portal.core.rgpd_masked_text_redirect")
        return data.replace(to_replace, replace_by)
