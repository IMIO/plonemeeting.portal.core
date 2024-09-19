# -*- coding: utf-8 -*-
from plone.app.content.browser.content_status_modify import ContentStatusModifyView
from plone.dexterity.browser.view import DefaultView
from plonemeeting.portal.core.browser.utils import path_to_dx_default_template
from Products.CMFCore.permissions import ModifyPortalContent
from Products.CMFCore.utils import _checkPermission
from plonemeeting.portal.core.utils import redirect
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


class MeetingContentStatusModifyView(ContentStatusModifyView):
    """Override to redirect back."""

    def __call__(self, workflow_action=None, comment="", effective_date=None, expiration_date=None, **kwargs):
        super().__call__(workflow_action, comment, effective_date, expiration_date, **kwargs)
        utils_view = self.context.restrictedTraverse("@@utils_view")
        return self.request.response.redirect(utils_view.get_meeting_url(meeting=self.context))

