# -*- coding: utf-8 -*-

from plone import api
from plone.autoform.form import AutoExtensibleForm
from z3c.form import button
from z3c.form.form import Form
from zope import schema
from zope.interface import Interface
import dateutil.parser
import json
import requests

from plonemeeting.portal.core import _
from plonemeeting.portal.core.utils import get_api_url_for_meetings


def sync_meeting(institution, meeting_data):
    meeting_UID = meeting_data.get("UID")
    meeting_date = meeting_data.get("date")
    meeting_title = meeting_data.get("title")
    brains = api.content.find(
        context=institution, portal_type="Meeting", plonemeeting_uid=meeting_UID
    )
    if not brains:
        with api.env.adopt_user("admin"):
            meeting = api.content.create(
                container=institution, type="Meeting", title=meeting_title
            )
        meeting.plonemeeting_uid = meeting_UID
    else:
        meeting = brains[0].getObject()
    meeting.title = meeting_title
    meeting.date_time = dateutil.parser.parse(meeting_date)  # XXX incorrect timezone
    meeting.reindexObject()
    return meeting


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
    def handleApply(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        institution = self.context
        url = get_api_url_for_meetings(institution, meeting_UID=data.get("meeting"))
        headers = {"Content-type": "application/json", "Accept": "application/json"}
        response = requests.get(
            url, auth=(institution.username, institution.password), headers=headers
        )
        if response.status_code != 200:
            self.status = _(u"Webservice connection error !")
            return

        json_meeting = json.loads(response.text)
        if json_meeting.get("items_total") != 1:
            self.status = _(u"Unexpected meeting count in webservice response !")
            return

        meeting = sync_meeting(institution, json_meeting.get("items")[0])
        self.status = _(u"Meeting imported !")

    @button.buttonAndHandler(_(u"Cancel"))
    def handleCancel(self, action):
        """
        """
        self.request.response.redirect(self.context.absolute_url())
