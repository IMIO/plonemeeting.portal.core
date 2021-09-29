# -*- coding: utf-8 -*-
from plone import api
from plone.api.portal import get_navigation_root
from plone.api.portal import get_registry_record
from plone.outputfilters.interfaces import IFilter
from plonemeeting.portal.core.config import DELIB_ANONYMIZED_TEXT
from plonemeeting.portal.core.config import RGPD_MASKED_TEXT
from zope.interface import implementer


@implementer(IFilter)
class ReplaceMaskedGDPR(object):
    order = 1000

    def __init__(self, context, request):
        self.context = context
        self.institution = get_navigation_root(self.context)
        self.request = request

    def is_enabled(self):
        return True

    def __call__(self, data):
        to_replace = get_registry_record("plonemeeting.portal.core.delib_masked_gdpr", default=DELIB_ANONYMIZED_TEXT)
        if not to_replace:  # get_registry_record may return None if record exists but empty
            to_replace = DELIB_ANONYMIZED_TEXT

        if self.institution.url_rgpd:
            redirect = self.institution.url_rgpd
        else:
            default = "#rgpd"
            base = api.portal.getSite().absolute_url()
            redirect = get_registry_record("plonemeeting.portal.core.rgpd_masked_text_redirect_path", default=default)
            if not redirect:  # get_registry_record may return None if record exists but empty
                redirect = default
            redirect = base + redirect

        placeholder = get_registry_record("plonemeeting.portal.core.rgpd_masked_text_placeholder",
                                          default=RGPD_MASKED_TEXT)
        if not placeholder:  # get_registry_record may return None if record exists but empty
            placeholder = RGPD_MASKED_TEXT
        replace_by = '<a class="pm-anonymize" href="{redirect}"><span>{placeholder}</span></a>'.format(
            redirect=redirect,
            placeholder=placeholder
        )
        return data.replace(to_replace, replace_by)
