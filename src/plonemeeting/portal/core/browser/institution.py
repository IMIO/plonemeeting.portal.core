# -*- coding: utf-8 -*-
from plone import api
from plone.app.z3cform.views import AddForm as DefaultAddForm
from plone.app.z3cform.views import DefaultAddView
from plone.app.z3cform.views import EditForm as DefaultEditForm
from plone.dexterity.browser.view import DefaultView
from plonemeeting.portal.core import _
from plonemeeting.portal.core.config import DEC_FOLDER_ID
from plonemeeting.portal.core.config import PUB_FOLDER_ID
from Products.CMFCore.permissions import ModifyPortalContent


class InstitutionView(DefaultView):
    """
    """
    def __call__(self):
        # Don't redirect if user can edit institution
        # Don't use api.user.has_permission since the method breaks robot tests
        if api.user.get_permissions(obj=self.context).get(ModifyPortalContent):
            api.portal.show_message(
                _(
                    "You see this page because you have permissions to edit it. "
                    "Otherwise you would have been redirected to Meetings folder. "
                    "To see the Meetings view, click on Meetings folder."
                ),
                request=self.request,
                type="info",
            )
            return super(InstitutionView, self).__call__()

        # redirect to "DEC_FOLDER_ID" if enabled, to "PUB_FOLDER_ID" if not
        # and to home page if nothing enabled
        utils_view = self.context.restrictedTraverse("@@utils_view")
        if DEC_FOLDER_ID in self.context.enabled_tabs:
            self.request.response.redirect(utils_view.get_meeting_url())
        elif PUB_FOLDER_ID in self.context.enabled_tabs:
            self.request.response.redirect(utils_view.get_publications_url())
        else:
            self.request.response.redirect(api.portal.get().absolute_url())
        return ""

    def _update(self):
        super(InstitutionView, self)._update()
        if 'password' in self.w:
            self.w['password'].value = self.context.password and '********************' or '-'

    def updateWidgets(self, prefix=None):
        super(InstitutionView, self).updateWidgets(prefix)


class AddForm(DefaultAddForm):
    portal_type = "Institution"

    def updateFields(self):
        super(AddForm, self).updateFields()

    def updateWidgets(self):
        super(AddForm, self).updateWidgets()


class AddView(DefaultAddView):
    form = AddForm


class EditForm(DefaultEditForm):
    portal_type = "Institution"

    def __call__(self):
        """ """
        # initializing form, we only have the _authenticator in request.form
        form_keys = tuple(self.request.form.keys())
        if not form_keys or form_keys == ('_authenticator',):
            self.context.fetch_delib_categories()
            self.context.fetch_delib_representatives()
        return super(EditForm, self).__call__()

    def updateFields(self):
        super(EditForm, self).updateFields()

    def updateWidgets(self):
        super(EditForm, self).updateWidgets()
