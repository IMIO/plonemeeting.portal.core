# -*- coding: utf-8 -*-

from imio.migrator.utils import end_time
from Products.Five import BrowserView
from plone import api
from plone.autoform.form import AutoExtensibleForm
from plonemeeting.portal.core.sync_utils import sync_meeting
from z3c.form import button
from z3c.form.form import Form
from zope import schema
from zope.interface import Interface

import time

from plonemeeting.portal.core import _
from plonemeeting.portal.core import logger
from plonemeeting.portal.core.interfaces import IMeetingsFolder


class IImportMeetingForm(Interface):
    """
    """

    meeting = schema.Choice(
        title=_(u"Meeting"),
        vocabulary="plonemeeting.portal.vocabularies.remote_meetings",
        required=True,
    )


class ImportMeetingForm(AutoExtensibleForm, Form):
    """
    """

    schema = IImportMeetingForm
    ignoreContext = True

    label = _(u"Meeting import form")
    description = _(u"Choose the meeting you want to import in the portal.")

    @button.buttonAndHandler(_(u"Import"))
    def handle_apply(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        institution = self.context
        meeting_uid = data.get("meeting")
        _sync_meeting(institution, meeting_uid, self.request)

    @button.buttonAndHandler(_(u"Cancel"))
    def handle_cancel(self, action):
        """
        """
        self.request.response.redirect(self.context.absolute_url())


class ImportMeetingView(BrowserView):  # pragma: no cover
    def import_meeting(self, force=False):
        meeting = self.context
        institution = meeting.aq_parent
        _sync_meeting(institution, meeting.plonemeeting_uid, self.request, force)


class SyncMeetingView(ImportMeetingView):  # pragma: no cover
    def __call__(self):
        self.import_meeting()


class ForceReimportMeetingView(ImportMeetingView):  # pragma: no cover
    def __call__(self):
        self.import_meeting(force=True)


def _sync_meeting(institution, meeting_uid, request, force=False):  # pragma: no cover
    try:
        start_time = time.time()
        logger.info("SYNC starting...")
        status, new_meeting_uid = sync_meeting(institution, meeting_uid, force)
        if new_meeting_uid:
            brains = api.content.find(
                context=institution, object_provides=IMeetingsFolder.__identifier__
            )

            if brains:
                request.response.redirect(
                    "{0}#seance={1}".format(brains[0].getURL(), new_meeting_uid)
                )
                api.portal.show_message(message=status, request=request, type="info")
        else:
            api.portal.show_message(message=status, request=request, type="error")
        logger.info(end_time(start_time, "SYNC PROCESSED IN "))
    except ValueError as error:
        api.portal.show_message(message=error.args[0], request=request, type="error")
