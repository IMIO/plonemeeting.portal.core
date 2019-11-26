# -*- coding: utf-8 -*-

from plone import api
from plone.app.textfield.value import RichTextValue
from plone.autoform.form import AutoExtensibleForm
from z3c.form import button
from z3c.form.form import Form
from zope import schema
from zope.component import getMultiAdapter
from zope.i18n import translate
from zope.interface import Interface

import dateutil.parser
import json
import requests

from plonemeeting.portal.core import _
from plonemeeting.portal.core.config import API_HEADERS
from plonemeeting.portal.core.interfaces import IMeetingsFolder
from plonemeeting.portal.core.utils import get_api_url_for_meeting_items
from plonemeeting.portal.core.utils import get_api_url_for_meetings


def format_attendees(meeting_data):
    assembly = ""
    assembly_excused = ""
    assembly_absents = ""
    if meeting_data.get("assembly").get("data") != "":
        assembly = "<b>{}:<b><br>{}".format(
            _("Attendees"), meeting_data.get("assembly").get("data")
        )
    if meeting_data.get("assemblyExcused").get("data") != "":
        assembly_excused = "<p><b>{}:</b><br>{}</p>".format(
            _("Excused"), meeting_data.get("assemblyExcused").get("data")
        )
    if meeting_data.get("assemblyAbsents").get("data") != "":
        assembly_absents = "<p><b>{}:</b><br>{}</p>".format(
            _("Absents"), meeting_data.get("assemblyAbsents").get("data")
        )
    formated_attendees = u"{} {} {}".format(
        assembly, assembly_excused, assembly_absents
    )
    return RichTextValue(formated_attendees, "text/html", "text/html")


def sync_items(to_localized_time, meeting, items_data):
    nb_created = nb_modified = nb_deleted = 0
    existing_items_brains = api.content.find(
        context=meeting, portal_type="Item", linkedMeetingUID=meeting.UID()
    )
    existing_items = {
        b.plonemeeting_uid: {"last_modified": b.plonemeeting_last_modified, "brain": b}
        for b in existing_items_brains
    }
    synced_uids = [i.get("UID") for i in items_data.get("items")]
    for item_data in items_data.get("items"):
        modification_date_str = item_data.get("modification_date")
        localized_time = to_localized_time(modification_date_str, long_format=1)
        modification_date = dateutil.parser.parse(localized_time)
        item_uid = item_data.get("UID")
        item_title = item_data.get("title")
        created = False
        if item_uid not in existing_items.keys():
            # Item must be created
            with api.env.adopt_user("admin"):
                item = api.content.create(
                    container=meeting, type="Item", title=item_title
                )
            item.plonemeeting_uid = item_uid
            created = True
        else:
            existing_last_modified = existing_items.get(item_uid).get("last_modified")
            if existing_last_modified and existing_last_modified >= modification_date:
                # Item must NOT be synced
                continue
            item = existing_items.get(item_uid).get("brain").getObject()

        # Sync item fields values
        item.plonemeeting_last_modified = modification_date
        item.title = item_title
        # TODO use formatted intem number when available
        item.number = str(item_data.get("itemNumber") / 100.0)
        item.representatives_in_charge = item_data.get("groupsInCharge")
        # TODO item.deliberation (with tal formatting)
        item.item_type = item_data.get("listType")
        item.category = item_data.get("category")
        item.reindexObject()
        if created:
            nb_created += 1
        else:
            nb_modified += 1

    # Delete existing items that have been removed in PM
    for uid, infos in existing_items.items():
        if uid not in synced_uids:
            obj = infos.get("brain").getObject()
            api.content.delete(obj)
            nb_deleted += 1

    return {"created": nb_created, "modified": nb_modified, "deleted": nb_deleted}


def sync_meeting(to_localized_time, institution, meeting_data):
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
    meeting.plonemeeting_last_modified = meeting_data.get("modification_date")
    meeting.attendees = format_attendees(meeting_data)
    meeting.title = meeting_title
    localized_time = to_localized_time(meeting_date, long_format=1)
    meeting.date_time = dateutil.parser.parse(localized_time)
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
        meeting_uid = data.get("meeting")
        current_lang = api.portal.get_default_language()[:2]
        to_localized_time = getMultiAdapter(
            (self.context, self.request), name="plone"
        ).toLocalizedTime
        url = get_api_url_for_meetings(institution, meeting_UID=meeting_uid)
        response = requests.get(
            url, auth=(institution.username, institution.password), headers=API_HEADERS
        )
        if response.status_code != 200:
            self.status = _(u"Webservice connection error !")
            return

        json_meeting = json.loads(response.text)
        if json_meeting.get("items_total") != 1:
            self.status = _(u"Unexpected meeting count in webservice response !")
            return

        meeting = sync_meeting(
            to_localized_time, institution, json_meeting.get("items")[0]
        )
        url = get_api_url_for_meeting_items(institution, meeting_UID=meeting_uid)
        response = requests.get(
            url, auth=(institution.username, institution.password), headers=API_HEADERS
        )
        if response.status_code != 200:
            self.status = _(u"Webservice connection error !")
            return

        json_items = json.loads(response.text)
        results = sync_items(to_localized_time, meeting, json_items)

        status_msg = _(
            u"meeting_imported",
            default=u"Meeting imported !  ${created} created items, ${modified} modified items, ${deleted} deleted items.",
            mapping={
                u"created": results["created"],
                u"modified": results["modified"],
                u"deleted": results["deleted"],
            },
        )
        self.status = translate(status_msg, target_language=current_lang)
        self._redirect_to_faceted(meeting.UID())

    @button.buttonAndHandler(_(u"Cancel"))
    def handleCancel(self, action):
        """
        """
        self.request.response.redirect(self.context.absolute_url())

    def _redirect_to_faceted(self, uid):
        """Redirect to the faceted view"""
        brains = api.content.find(
            context=self.context, object_provides=IMeetingsFolder.__identifier__
        )
        if brains:
            self.request.response.redirect(
                "{0}#seance={1}".format(brains[0].getURL(), uid)
            )
