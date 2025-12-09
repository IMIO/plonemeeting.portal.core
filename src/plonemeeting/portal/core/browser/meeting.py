# -*- coding: utf-8 -*-
from plone.dexterity.browser.view import DefaultView
from plonemeeting.portal.core import _
from plonemeeting.portal.core.browser import BaseAddForm
from plonemeeting.portal.core.browser import BaseEditForm
from plonemeeting.portal.core.browser.utils import path_to_dx_default_template
from Products.CMFCore.permissions import ModifyPortalContent
from Products.CMFCore.utils import _checkPermission
from z3c.form import button
from zope.browserpage import ViewPageTemplateFile


class MeetingForm:
    zope_admin_fieldsets = ["settings", "ownership", "dates", "categorization"]


class MeetingAddForm(MeetingForm, BaseAddForm):
    """
    """

    def updateFields(self):
        helper = self.context.unrestrictedTraverse("@@utils_view")
        if not helper.is_in_institution():
            return  # Should not happen
        institution = helper.get_current_institution()
        super(MeetingAddForm, self).updateFields()
        self.fields['custom_info'].field.default = institution.default_meeting_extra_infos_text


class MeetingEditForm(MeetingForm, BaseEditForm):
    """
    """

    @button.buttonAndHandler(_("Save"), name="save")
    def handleApply(self, action):
        super(MeetingEditForm, self).handleApply(self, action)
        utils_view = self.context.restrictedTraverse("@@utils_view")
        self.request.response.redirect(utils_view.get_meeting_url(meeting=self.context))

    @button.buttonAndHandler(_("Cancel"), name="cancel")
    def handleCancel(self, action):
        super(MeetingEditForm, self).handleCancel(self, action)
        utils_view = self.context.restrictedTraverse("@@utils_view")
        self.request.response.redirect(utils_view.get_meeting_url(meeting=self.context))


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
