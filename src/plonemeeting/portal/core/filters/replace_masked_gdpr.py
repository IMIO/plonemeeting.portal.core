# -*- coding: utf-8 -*-
from plone import api
from plone.api.portal import get_navigation_root
from plone.api.portal import get_registry_record
from plone.outputfilters.interfaces import IFilter
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
        to_replace = get_registry_record("plonemeeting.portal.core.delib_masked_gdpr")
        if self.institution.url_rgpd:
            redirect = self.institution.url_rgpd
        else:
            base = api.portal.getSite().absolute_url()
            redirect = base + get_registry_record("plonemeeting.portal.core.rgpd_masked_text_redirect_path")

        placeholder = get_registry_record("plonemeeting.portal.core.rgpd_masked_text_placeholder")
        replace_by = '<a class="pm-anonymize" href="{redirect}"><span>{placeholder}</span></a>'.format(
            redirect=redirect,
            placeholder=placeholder
        )
        return data.replace(to_replace, replace_by)
