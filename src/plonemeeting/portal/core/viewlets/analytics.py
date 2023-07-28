# -*- coding: utf-8 -*-
from collective.cookiecuttr.browser.viewlet import CookieCuttrAwareAnalyticsViewlet
from plone import api
from plonemeeting.portal.core.content.institution import IInstitution


class PMAnalyticsViewlet(CookieCuttrAwareAnalyticsViewlet):
    @property
    def webstats_js(self):
        navroot = api.portal.get_navigation_root(self.context)
        if (
            IInstitution.providedBy(navroot)
            and hasattr(navroot, "webstats_js")
            and navroot.webstats_js
        ):
            return navroot.webstats_js
        else:
            return super().webstats_js
