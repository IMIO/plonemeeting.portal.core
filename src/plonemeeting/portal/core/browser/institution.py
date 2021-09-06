# -*- coding: utf-8 -*-
from plone import api
from plone.dexterity.browser import add
from plone.dexterity.browser import edit
from plone.dexterity.browser.view import DefaultView
from plonemeeting.portal.core import _
from plonemeeting.portal.core.interfaces import IMeetingsFolder
from zope.browserpage import ViewPageTemplateFile

import os
import plone


def _path_to_dx_default_template():
    dx_path = os.path.dirname(plone.dexterity.browser.__file__)
    return os.path.join(dx_path, "item.pt")


class InstitutionView(DefaultView):
    """
    """
    index = ViewPageTemplateFile(_path_to_dx_default_template())

    def __call__(self):
        # Don't redirect if user can edit institution
        # Don't use api.user.has_permission since the method breaks robot tests
        if api.user.get_permissions(obj=self.context).get("Modify portal content"):
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

        institution = api.portal.get_navigation_root(self.context)
        meeting_folder_brains = api.content.find(
            context=institution, object_provides=IMeetingsFolder.__identifier__
        )
        if not meeting_folder_brains:
            return super(InstitutionView, self).__call__()
        url = meeting_folder_brains[0].getURL()
        self.request.response.redirect(url)
        return ""

    def updateWidgets(self, prefix=None):
        super(InstitutionView, self).updateWidgets(prefix)
        self.widgets['password'].value = self.context.password and '********************' or '-'


class AddForm(add.DefaultAddForm):
    portal_type = "Institution"

    def updateFields(self):
        super(AddForm, self).updateFields()

    def updateWidgets(self):
        super(AddForm, self).updateWidgets()


class AddView(add.DefaultAddView):
    form = AddForm


class EditForm(edit.DefaultEditForm):
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
