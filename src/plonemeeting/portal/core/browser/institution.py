# -*- coding: utf-8 -*-
from plone import api
from plone.dexterity.browser.add import DefaultAddForm
from plone.dexterity.browser.add import DefaultAddView
from plone.dexterity.browser.edit import DefaultEditForm
from plone.dexterity.browser.view import DefaultView
from plone.dexterity.events import EditCancelledEvent
from plone.dexterity.events import EditFinishedEvent
from plonemeeting.portal.core import _
from plonemeeting.portal.core.config import DEC_FOLDER_ID
from plonemeeting.portal.core.config import PUB_FOLDER_ID
from Products.statusmessages.interfaces import IStatusMessage
from z3c.form import button
from zope.event import notify


class InstitutionView(DefaultView):
    """ """

    def __call__(self):
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


class InstitutionSettingsView(DefaultView):
    """ """

    _actions = {
        "edit": {
            "title": _("Edit"),
            "url": "${context}/edit",
            "icon": "pencil",
            "condition": "python: ",
        },
    }

    _navigation_links = {
        "manage-users": {
            "title": _("label_manage_users"),
            "url": "@@manage-users",
            "icon": "people",
        },
        "manage-templates": {
            "title": _("label_manage_templates"),
            "url": "@@manage-templates",
            "icon": "file-text",
        },
    }

    def _update(self):
        super(InstitutionSettingsView, self)._update()
        if "password" in self.w:
            self.w["password"].value = self.context.password and "********************" or "-"

    def updateWidgets(self, prefix=None):
        super(InstitutionSettingsView, self).updateWidgets(prefix)


class AddForm(DefaultAddForm):
    portal_type = "Institution"

    def updateFields(self):
        super(AddForm, self).updateFields()

    def updateWidgets(self, prefix=None):
        super(AddForm, self).updateWidgets(prefix)


class AddView(DefaultAddView):
    form = AddForm


class EditForm(DefaultEditForm):
    portal_type = "Institution"

    def __call__(self):
        """ """
        # initializing form, we only have the _authenticator in request.form
        form_keys = tuple(self.request.form.keys())
        if not form_keys or form_keys == ("_authenticator",):
            self.context.fetch_delib_categories()
            self.context.fetch_delib_representatives()
        return super(EditForm, self).__call__()

    def updateFields(self):
        super(EditForm, self).updateFields()

    def updateWidgets(self, prefix=None):
        super(EditForm, self).updateWidgets(prefix)

    def updateActions(self):
        super().updateActions()
        self.actions["save_no_inline_validation"].klass = "submit-widget btn btn-primary"

    @button.buttonAndHandler(_("Save"), name="save_no_inline_validation")
    # We need to override the handleApply method to redirect to the settings view
    # Also, the name cannot be set to "save" or "add" to avoid inline validation.
    # TODO : find another way to avoid inline validation.
    def handleApply(self, action):  # pragma: no cover
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        self.applyChanges(data)
        IStatusMessage(self.request).addStatusMessage(self.success_message, "info")
        self.request.response.redirect(f"{self.context.absolute_url()}/@@manage-settings")
        notify(EditFinishedEvent(self.context))

    @button.buttonAndHandler(_("Cancel"), name="cancel")
    def handleCancel(self, action):  # pragma: no cover
        IStatusMessage(self.request).addStatusMessage(_("Edit cancelled"), "info")
        self.request.response.redirect(f"{self.context.absolute_url()}/@@manage-settings")
        notify(EditCancelledEvent(self.context))
