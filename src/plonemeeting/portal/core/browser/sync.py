# -*- coding: utf-8 -*-
from Products.Five import BrowserView
from plone import api
from plone.app.textfield.value import RichTextValue
from plone.autoform.form import AutoExtensibleForm
from Products.CMFCore.Expression import Expression, getExprContext
from plone.namedfile.file import NamedBlobFile
from z3c.form import button
from z3c.form.form import Form
from zope import schema
from zope.i18n import translate
from zope.interface import Interface

import dateutil.parser
import json
import pytz
import requests

from plonemeeting.portal.core import _
from plonemeeting.portal.core.config import API_HEADERS
from plonemeeting.portal.core.interfaces import IMeetingsFolder
from plonemeeting.portal.core.utils import get_api_url_for_meeting_items
from plonemeeting.portal.core.utils import get_api_url_for_meetings
from plonemeeting.portal.core.utils import get_global_category


def _call_delib_rest_api(url, institution):
    response = requests.get(
        url, auth=(institution.username, institution.password), headers=API_HEADERS
    )

    if response.status_code != 200:
        raise ValueError(_(u"Webservice connection error !"))

    return response


def _json_date_to_datetime(datetime_json):
    date_time = dateutil.parser.parse(datetime_json)
    timezone = api.portal.get_registry_record("plone.portal_timezone")
    return date_time.astimezone(pytz.timezone(timezone))


def get_formatted_data_from_json(tal_expression, item, item_data):
    if not tal_expression:
        return None
    expression = Expression(tal_expression)
    expression_context = getExprContext(item)
    expression_context.vars["json"] = item_data
    expression_result = expression(expression_context)
    return expression_result


def sync_annexes_data(item, institution, annexes_json):
    existing_annexes = item.listFolderContents(contentFilter={"portal_type": "File"})

    def get_annex_if_exists(pm_uid):
        for existing_annex_obj in existing_annexes:
            if existing_annex_obj.plonemeeting_uid == pm_uid:
                return existing_annex_obj
        return None

    def annex_should_be_updated(annex_obj, pm_last_modified):
        import ipdb

        ipdb.set_trace()
        return (
            not hasattr(annex_obj, "plonemeeting_last_modified")
            or annex.plonemeeting_last_modified < pm_last_modified
        )

    for annex_data in annexes_json:
        annex_pm_uid = annex_data.get("UID")
        publishable_activated = annex_data.get("publishable_activated")
        publishable = annex_data.get("publishable")
        annex = get_annex_if_exists(annex_pm_uid)

        # download all annexes except if annex publication is enabled in ia.Delib AND this annex not publishable
        if not publishable_activated or publishable:
            # if it's a new annex or if it has been modified since last sync, then set all attributes
            annex_pm_last_modified = _json_date_to_datetime(annex_data.get("modified"))
            if (
                annex and annex_should_be_updated(annex, annex_pm_last_modified)
            ) or not annex:
                file_title = annex_data.get("category_title")
                if not annex:
                    annex = api.content.create(
                        container=item, type="File", title=file_title
                    )
                file_json = annex_data.get("file")
                dl_link = file_json.get("download")
                file_content_type = file_json.get("content-type")

                response = _call_delib_rest_api(dl_link, institution)
                file_blob = response.content

                file_name = u"{}.{}".format(
                    annex.id, file_json.get("filename").split(".")[-1]
                )
                annex.file = NamedBlobFile(
                    data=file_blob, contentType=file_content_type, filename=file_name
                )
                annex.plonemeeting_uid = annex_pm_uid
                annex.plonemeeting_last_modified = annex_pm_last_modified
                annex.reindexObject()

            for existing_annex in existing_annexes:
                if annex_pm_uid == existing_annex.plonemeeting_uid:
                    existing_annexes.remove(existing_annex)
                    break
    # delete leftovers
    for existing_annex in existing_annexes:
        api.content.delete(existing_annex)


def sync_annexes(item, institution, annexes_json):
    if annexes_json:
        response = _call_delib_rest_api(annexes_json.get("@id"), institution)
        sync_annexes_data(item, institution, response.json())


def sync_items_data(meeting, items_data, institution, force=False):
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
        modification_date = _json_date_to_datetime(item_data.get("modification_date"))
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
            if (
                not force
                and existing_last_modified
                and existing_last_modified >= modification_date
            ):
                # Item must NOT be synced
                continue
            item = existing_items.get(item_uid).get("brain").getObject()

        # Sync item fields values
        item.plonemeeting_last_modified = modification_date
        item.title = item_title
        formatted_title = get_formatted_data_from_json(
            institution.item_title_formatting_tal, item, item_data
        )
        if formatted_title is not None:
            item.formatted_title = RichTextValue(
                formatted_title, "text/html", "text/html"
            )

        item.number = item_data.get("formatted_itemNumber")
        item.representatives_in_charge = item_data.get(
            "groupsInCharge"
        ) or item_data.get("all_groupsInCharge")

        item.decision = RichTextValue(
            get_formatted_data_from_json(
                institution.item_decision_formatting_tal, item, item_data
            ),
            "text/html",
            "text/html",
        )

        item.additional_data = RichTextValue(
            get_formatted_data_from_json(
                institution.item_additional_data_formatting_tal, item, item_data
            ),
            "text/html",
            "text/html",
        )

        item.category = get_global_category(
            meeting.aq_parent, item_data.get("category")
        )
        item.reindexObject()
        sync_annexes(item, institution, item_data.get("@components").get("annexes"))
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


def sync_meeting_data(institution, meeting_data):
    meeting_uid = meeting_data.get("UID")
    meeting_title = meeting_data.get("title")
    brains = api.content.find(
        context=institution, portal_type="Meeting", plonemeeting_uid=meeting_uid
    )
    if not brains:
        with api.env.adopt_user("admin"):
            meeting = api.content.create(
                container=institution, type="Meeting", title=meeting_title
            )
        meeting.plonemeeting_uid = meeting_uid
    else:
        meeting = brains[0].getObject()
    meeting.plonemeeting_last_modified = _json_date_to_datetime(
        meeting_data.get("modification_date")
    )
    meeting.title = meeting_title
    meeting.date_time = _json_date_to_datetime(meeting_data.get("date"))
    meeting.reindexObject()
    return meeting


def sync_meeting(institution, meeting_uid, force=False):
    """
    synchronizes a single meeting through ia.Delib web services (Rest/JSON)
    :param force: Should force reload items. Default False
    :param institution: current institution
    :param meeting_uid: the uid of the meeting to fetch from ia.Delib
    :return: the sync status, the new meeting's UID
    status may be an error or a short summary of what happened.
    UID may be none in case of error from the web service
    """
    url = get_api_url_for_meetings(institution, meeting_UID=meeting_uid)
    response = _call_delib_rest_api(url, institution)

    if response.status_code != 200:
        return _(u"Webservice connection error !"), None

    json_meeting = json.loads(response.text)
    if json_meeting.get("items_total") != 1:
        return _(u"Unexpected meeting count in webservice response !"), None

    meeting = sync_meeting_data(institution, json_meeting.get("items")[0])
    url = get_api_url_for_meeting_items(institution, meeting_UID=meeting_uid)
    response = _call_delib_rest_api(url, institution)
    if response.status_code != 200:
        return _(u"Webservice connection error !"), None

    json_items = json.loads(response.text)
    results = sync_items_data(meeting, json_items, institution, force)

    status_msg = _(
        u"meeting_imported",
        default=u"Meeting imported !  "
        u"${created} created items, "
        u"${modified} modified items, "
        u"${deleted} deleted items.",
        mapping={
            u"created": results["created"],
            u"modified": results["modified"],
            u"deleted": results["deleted"],
        },
    )
    current_lang = api.portal.get_default_language()[:2]
    status = translate(status_msg, target_language=current_lang)
    return status, meeting.UID()


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
        self.status, new_meeting_uid = sync_meeting(institution, meeting_uid)
        _handle_sync_meeting_response(
            new_meeting_uid, self.request, self.context, self.status
        )

    @button.buttonAndHandler(_(u"Cancel"))
    def handle_cancel(self, action):
        """
        """
        self.request.response.redirect(self.context.absolute_url())


class ReimportMeetingView(BrowserView):
    def __call__(self):
        meeting = self.context
        institution = meeting.aq_parent
        status, new_meeting_uid = sync_meeting(
            institution, meeting.plonemeeting_uid, force=True
        )
        _handle_sync_meeting_response(
            new_meeting_uid, self.request, institution, status
        )


def _handle_sync_meeting_response(
    new_meeting_uid, request, institution, status_message
):
    if new_meeting_uid:
        _redirect_to_faceted(new_meeting_uid, request, institution, status_message)
    else:
        api.portal.show_message(message=status_message, request=request, type="error")


def _redirect_to_faceted(uid, request, institution, status_message):
    """Redirect to the faceted view"""

    brains = api.content.find(
        context=institution, object_provides=IMeetingsFolder.__identifier__
    )

    if brains:
        request.response.redirect("{0}#seance={1}".format(brains[0].getURL(), uid))
        api.portal.show_message(message=status_message, request=request, type="info")
