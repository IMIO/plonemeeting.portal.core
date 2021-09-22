# -*- coding: utf-8 -*-

from plone import api
from plone.app.layout.viewlets.common import LogoViewlet
from plonemeeting.portal.core.content.institution import IInstitution


class PMLogoViewlet(LogoViewlet):
    def update(self):
        super(PMLogoViewlet, self).update()

        nav_root = api.portal.get_navigation_root(self.context)
        if IInstitution.providedBy(nav_root):
            if not nav_root.logo:
                return
            self.navigation_root_title = nav_root.title
            self.logo_title = nav_root.title
            self.img_src = u"{0}/@@images/logo".format(nav_root.absolute_url())
