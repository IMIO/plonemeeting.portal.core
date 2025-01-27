# -*- coding: utf-8 -*-

from imio.helpers.content import richtextval
from imio.migrator.utils import end_time
from plone import api
from plone.app.uuid.utils import uuidToObject
from plone.namedfile.file import NamedBlobFile
from plonemeeting.portal.core import _
from plonemeeting.portal.core import logger
from plonemeeting.portal.core.config import API_HEADERS
from plonemeeting.portal.core.config import DEC_FOLDER_ID
from plonemeeting.portal.core.utils import get_api_url_for_annexes
from plonemeeting.portal.core.utils import get_api_url_for_meeting_items
from plonemeeting.portal.core.utils import get_api_url_for_meetings
from plonemeeting.portal.core.utils import get_global_category
from Products.CMFCore.Expression import Expression
from Products.CMFCore.Expression import getExprContext
from zope.i18n import translate

import dateutil.parser
import json
import pytz
import requests
import time


def _call_delib_rest_api(url, institution):  # pragma: no cover
    start_time = time.time()
    logger.info("REST API CALL TO {0}".format(url))
    response = requests.get(
        url, auth=(institution.username, institution.password), headers=API_HEADERS
    )

    if response.status_code != 200:
        logger.error("Response status_code was not 200 : {}".format(response.status_code))
        raise ValueError(_(u"Web service connection error !"))
    msg, seconds = end_time(start_time, "REST API CALL MADE IN ", True)
    if seconds > 1:
        logger.warning(msg)
    else:
        logger.info(msg)

    return response


def _json_date_to_datetime(datetime_json):
    date_time = dateutil.parser.parse(datetime_json)
    timezone = api.portal.get_registry_record("plone.portal_timezone")
    return date_time.astimezone(pytz.timezone(timezone))


def _get_mapped_representatives_in_charge(item_data, institution):
    """
    Ensure that only mapped representatives in charge are kept when syncing
    """
    groups_in_charge = item_data.get(
        "groupsInCharge"
    ) or item_data.get("all_groupsInCharge")

    res = []
    if groups_in_charge and institution.representatives_mappings:
        gic_tokens = [gic["token"] for gic in groups_in_charge]
        mapped_uids = [mapping["representative_key"] for mapping in institution.representatives_mappings]
        res = list(filter(lambda uid: uid in mapped_uids, gic_tokens))
    return res


def get_formatted_data_from_json(tal_expression, item, item_data):
    if not tal_expression:
        return None
    expression = Expression(tal_expression)
    expression_context = getExprContext(item)
    expression_context.vars["json"] = item_data
    expression_result = expression(expression_context)
    return expression_result


def sync_annexes_data(item, institution, annexes_json, force=False):
    existing_annexes = item.listFolderContents(contentFilter={"portal_type": "File"})

    def get_annex_if_exists(pm_uid):
        for existing_annex_obj in existing_annexes:
            if existing_annex_obj.plonemeeting_uid == pm_uid:
                return existing_annex_obj
        return None

    def annex_should_be_updated(annex_obj, pm_last_modified):
        return (
            force
            or not hasattr(annex_obj, "plonemeeting_last_modified")
            or annex.plonemeeting_last_modified < pm_last_modified
        )

    # we receive only publishable annexes
    for annex_data in annexes_json:
        if not annex_data.get("publishable", False):
            # Make sure we have publishable annexes. Otherwise, we abort and notify the user.
            raise ValueError(_(u"Unexpected publishable annex value in web service response !"))

        annex_pm_uid = annex_data.get("UID")
        annex = get_annex_if_exists(annex_pm_uid)

        # if it's a new annex or if it has been modified since last sync, then set all attributes
        annex_pm_last_modified = _json_date_to_datetime(annex_data.get("modified"))
        if (
            annex and annex_should_be_updated(annex, annex_pm_last_modified)
        ) or not annex:
            file_title = get_formatted_data_from_json(
                institution.info_annex_formatting_tal, item, annex_data
            ) or annex_data.get("title")
            if annex:
                annex.title = file_title
            else:
                annex = api.content.create(
                    container=item, type="File", title=file_title
                )
            file_json = annex_data.get("file")
            dl_link = file_json.get("download")
            file_content_type = file_json.get("content-type")

            response = _call_delib_rest_api(dl_link, institution)
            file_blob = response.content

            # in some rare cases, filename can be None
            json_filename = file_json.get("filename") or "default_filename.pdf"
            file_name = u"{}.{}".format(annex.id, json_filename.split(".")[-1])
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
    with api.env.adopt_roles(["Manager"]):
        for existing_annex in existing_annexes:
            api.content.delete(existing_annex)


def sync_annexes(item, institution, item_json_id, force=False):  # pragma: no cover
    # item_json_id is the "@id" value
    if item_json_id:
        url = get_api_url_for_annexes(item_json_id)
        response = _call_delib_rest_api(url, institution)
        sync_annexes_data(item, institution, response.json(), force)


def sync_items_number(item_dict):
    """
    :param item_dict: a dict of dict with the following structure :
        {'item_uid': {'sortable_number': 100, 'number': '1'}, ...}
    :return: the number of updated items.
    """
    modified = 0
    for item_uid in item_dict.keys():
        item = uuidToObject(item_uid)
        new_item_sortable_number = item_dict[item_uid]['sortable_number']
        new_item_number = item_dict[item_uid]['number']
        was_modified = _sync_item_number(item, new_item_sortable_number, new_item_number)
        if was_modified:
            modified += 1
    return modified


def _sync_item_number(item, new_item_sortable_number, new_item_number):
    if new_item_sortable_number != item.sortable_number:
        item.sortable_number = new_item_sortable_number
        item.number = new_item_number
        item.reindexObject(idxs=['number', 'sortable_number'])
        return True
    return False


def sync_items_data(meeting, items_data, institution, force=False, with_annexes=True, item_external_uids=[]):
    nb_created = nb_modified = nb_deleted = 0
    if item_external_uids:
        existing_items_brains = api.content.find(
            context=meeting, portal_type="Item", linkedMeetingUID=meeting.UID(), plonemeeting_uid=item_external_uids
        )
    else:
        existing_items_brains = api.content.find(
            context=meeting, portal_type="Item", linkedMeetingUID=meeting.UID()
        )
    existing_items = {
        b.plonemeeting_uid: {"last_modified": b.plonemeeting_last_modified,
                             "brain": b,
                             "sortable_number": b.sortable_number}
        for b in existing_items_brains
    }
    synced_uids = [i.get("UID") for i in items_data.get("items")]

    for item_data in items_data.get("items"):
        # XXX compatibility, with DX there is no "modification_date" anymore
        # so depending MeetingItem is AT or DX, try to get modification_date or modified
        modification_date = _json_date_to_datetime(
            item_data.get("modification_date", item_data.get("modified"))
        )
        sortable_number = item_data["itemNumber"]

        item_uid = item_data.get("UID")
        item_title = item_data.get("title")
        created = False
        if item_uid not in existing_items.keys():
            # Item must be created
            with api.env.adopt_roles(["Manager"]):
                item = api.content.create(
                    container=meeting, type="Item", title=item_title
                )
            item.plonemeeting_uid = item_uid
            created = True
        else:
            existing_last_modified = existing_items.get(item_uid).get("last_modified")
            existing_sortable_number = existing_items.get(item_uid).get("sortable_number")
            if (
                not force
                and existing_last_modified
                and existing_last_modified >= modification_date
                and sortable_number
                and sortable_number == existing_sortable_number
            ):
                # Item must NOT be synced
                continue
            item = existing_items.get(item_uid).get("brain").getObject()

        _sync_item_number(item, item_data["itemNumber"], item_data["formatted_itemNumber"])

        if force or item.plonemeeting_last_modified is None or item.plonemeeting_last_modified < modification_date:
            # Sync item fields values
            item.plonemeeting_last_modified = modification_date
            # reinit formatted title in case the configuration changed in portal
            item.formatted_title = None
            item.title = item_title
            formatted_title = get_formatted_data_from_json(
                institution.item_title_formatting_tal, item, item_data
            )
            if formatted_title:
                item.formatted_title = richtextval(formatted_title)
            else:
                item.formatted_title = richtextval("<p>" + item_title + "</p>")

            representative_uid = _get_mapped_representatives_in_charge(item_data, institution)
            item.representatives_in_charge = representative_uid
            item.long_representatives_in_charge = representative_uid

            item.decision = richtextval(
                get_formatted_data_from_json(
                    institution.item_decision_formatting_tal, item, item_data
                )
            )

            item.additional_data = richtextval(
                get_formatted_data_from_json(
                    institution.item_additional_data_formatting_tal, item, item_data
                ),
            )

            item.category = get_global_category(
                institution, item_data.get(institution.delib_category_field)["token"]
            )
            item.reindexObject()
            if with_annexes:
                sync_annexes(
                    item, institution, item_data.get("@id"), force
                )
        if created:
            nb_created += 1
        else:
            nb_modified += 1

    # Delete existing items that have been removed in PM
    with api.env.adopt_roles(["Manager"]):
        for uid, infos in existing_items.items():
            if uid not in synced_uids:
                obj = infos.get("brain").getObject()
                api.content.delete(obj)
                nb_deleted += 1

    return {"created": nb_created, "modified": nb_modified, "deleted": nb_deleted}


def sync_meeting_data(institution, meeting_data):
    meeting_uid = meeting_data.get("UID")
    meeting_title = meeting_data.get("title")
    decisions = institution[DEC_FOLDER_ID]
    brains = api.content.find(
        context=decisions, portal_type="Meeting", plonemeeting_uid=meeting_uid
    )
    if not brains:
        with api.env.adopt_roles(["Manager"]):
            meeting = api.content.create(
                container=decisions, type="Meeting", title=meeting_title
            )
        meeting.plonemeeting_uid = meeting_uid
    else:
        meeting = brains[0].getObject()
    # XXX compatibility, with DX there is no more "modification_date"
    # so depending Meeting is AT or DX, try to get modification_date or modified
    meeting.plonemeeting_last_modified = _json_date_to_datetime(
        meeting_data.get("modification_date", meeting_data.get("modified"))
    )
    meeting.title = meeting_title
    meeting.date_time = _json_date_to_datetime(meeting_data.get("date"))
    meeting.reindexObject()
    return meeting


def sync_meeting(institution, meeting_external_uid, force=False, with_annexes=True, item_external_uids=[]):
    """
    synchronizes a single meeting through ia.Delib web services (Rest/JSON)
    :param force: Should force reload items. Default False
    :param institution: current institution folder
    :param meeting_external_uid: the uid of the meeting to fetch from ia.Delib
    :param item_external_uids: the list of meeting item uids to fetch from ia.Delib. Leave empty to sync all of them.
    :return: the sync status, the new meeting's UID
    status may be an error or a short summary of what happened.
    UID may be none in case of error from the web service
    """
    url = get_api_url_for_meetings(institution, meeting_external_uid=meeting_external_uid)
    response = _call_delib_rest_api(url, institution)

    json_meeting = json.loads(response.text)
    if json_meeting.get("items_total") != 1:
        raise ValueError(_(u"Unexpected meeting count in web service response !"))

    meeting = sync_meeting_data(institution, json_meeting.get("items")[0])
    url = get_api_url_for_meeting_items(institution,
                                        meeting_external_uid=meeting_external_uid,
                                        item_external_uids=item_external_uids)
    response = _call_delib_rest_api(url, institution)

    json_items = json.loads(response.text)
    results = sync_items_data(meeting, json_items, institution,
                              force=force,
                              with_annexes=with_annexes,
                              item_external_uids=item_external_uids)

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
