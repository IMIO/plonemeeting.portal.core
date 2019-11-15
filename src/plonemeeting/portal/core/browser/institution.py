# -*- coding: utf-8 -*-

from plone import api
from plone.dexterity.browser.view import DefaultView

from plonemeeting.portal.core import _
from plonemeeting.portal.core.interfaces import IMeetingsFolder


class InstitutionView(DefaultView):
    """
    """

    def __call__(self):
        # Don't redirect if user can edit institution
        user = api.user.get_current()
        if api.user.has_permission(
            "Modify portal content", user=user, obj=self.context
        ):
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
            context=institution,
            object_provides=IMeetingsFolder.__identifier__
        )
        if not meeting_folder_brains:
            return super(InstitutionView, self).__call__()
        url = meeting_folder_brains[0].getURL()
        self.request.response.redirect(url)
        return ""
