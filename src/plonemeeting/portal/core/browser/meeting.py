# -*- coding: utf-8 -*-

from plone.dexterity.browser.view import DefaultView
from plonemeeting.portal.core.browser.utils import path_to_dx_default_template
from Products.CMFCore.permissions import ModifyPortalContent
from Products.CMFCore.utils import _checkPermission
from zope.browserpage import ViewPageTemplateFile


class MeetingView(DefaultView):
    """
    """
    index = ViewPageTemplateFile(path_to_dx_default_template())

    def __call__(self):
        # Don't redirect if user can view meeting backoffice
        if _checkPermission(ModifyPortalContent, self.context):
            return super(MeetingView, self).__call__()

        utils_view = self.context.restrictedTraverse("@@utils_view")
        self.request.response.redirect(utils_view.get_meeting_url(meeting=self.context))
        return ""
