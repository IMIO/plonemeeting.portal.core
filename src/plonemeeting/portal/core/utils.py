# -*- coding: utf-8 -*-
from Products.CMFPlone.interfaces.constrains import ISelectableConstrainTypes
from Products.CMFPlone.utils import safe_unicode
from plone import api
from plone.app.textfield.value import IRichTextValue
from plone.portlets.interfaces import IPortletAssignmentMapping
from plone.portlets.interfaces import IPortletManager
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.globalrequest import getRequest
from zope.i18n import translate
from zope.interface import provider
from zope.schema.interfaces import IContextAwareDefaultFactory

from plonemeeting.portal.core import _
from plonemeeting.portal.core.config import CONTENTS_TO_CLEAN
from plonemeeting.portal.core.config import PLONEMEETING_API_MEETING_TYPE
from plonemeeting.portal.core.config import PLONEMEETING_API_ITEM_TYPE


def format_institution_managers_group_id(institution):
    return "{0}-institution_managers".format(institution.id)


def get_text_from_richtext(field):  # pragma: no cover
    if IRichTextValue.providedBy(field):
        transforms = api.portal.get_tool("portal_transforms")
        raw = safe_unicode(field.raw)
        text = (
            transforms.convertTo("text/plain", raw, mimetype=field.mimeType)
            .getData()
            .strip()
        )
        return safe_unicode(text)


def default_translator(msgstring, **replacements):  # pragma: no cover
    @provider(IContextAwareDefaultFactory)
    def context_provider(context):
        value = translate(msgstring, context=getRequest())
        if replacements:
            value = value.format(**replacements)
        return value

    return context_provider


def get_api_url_for_meetings(institution, meeting_external_uid=None):
    if not institution.plonemeeting_url or not institution.meeting_config_id:
        return
    url = (
        "{0}/@search?"
        "type={1}"
        "&config_id={2}".format(
            institution.plonemeeting_url.rstrip("/"),
            PLONEMEETING_API_MEETING_TYPE,
            institution.meeting_config_id,
        )
    )
    if meeting_external_uid:
        url = "{0}" \
              "{1}" \
              "&fullobjects=True" \
              "&include_all=false" \
              "&metadata_fields=date" \
              "&b_size=9999".format(url, _get_uids_filter_url([meeting_external_uid]))
    else:
        url = "{0}{1}".format(url, institution.additional_meeting_query_string_for_list)
    return url


def _get_category_filter_url(institution):
    if institution.delib_category_field == "category":
        url_param = "&getCategory="
    else:
        url_param = "&getRawClassifier="

    return _get_url_filter(url_param,
                           institution.categories_mappings,
                           'local_category_id',
                           use_void_value=True)


def _get_representatives_filter_url(institution):
    return _get_url_filter("&getGroupsInCharge=",
                           institution.representatives_mappings,
                           'representative_key')


def _get_url_filter(url_param, value_dict_list, dict_key, use_void_value=False):
    if not value_dict_list:
        if use_void_value:
            return "{}VOID".format(url_param)
        else:
            return ""

    values = []
    for mapping in value_dict_list:
        values.append(mapping[dict_key])

    res = url_param + url_param.join(values)
    return res


def _get_uids_filter_url(uids):
    if uids:
        url_param = "&UID="
        return url_param + url_param.join(uids)
    else:
        return ""


def get_api_url_for_annexes(item_json_id):
    url = "{0}/@annexes?" \
          "publishable=true" \
          "&fullobjects" \
          "&include_all=false" \
          "&metadata_fields=file" \
          "&metadata_fields=content_category" \
          "&additional_values=category_title" \
          "&additional_values=subcategory_title".format(item_json_id)
    return url


def get_api_url_for_meeting_items(institution,
                                  meeting_external_uid,
                                  item_external_uids=[],
                                  with_additional_published_items_query_string=True):
    if not institution.plonemeeting_url or not institution.meeting_config_id:
        return
    category_filter = _get_category_filter_url(institution)
    representatives_filter = _get_representatives_filter_url(institution)
    item_uids_filter = _get_uids_filter_url(item_external_uids)
    # XXX linkedMeetingUID/meeting_uid compatibility, index was renamed to meeting_uid
    url = (
        "{plonemeeting_url}/@search?"
        "type={type}"
        "&sort_on=getItemNumber"
        "&privacy=public"
        "&privacy=public_heading"
        "&b_size=9999"
        "&additional_values=formatted_itemNumber"
        "&config_id={meeting_config_id}"
        "&linkedMeetingUID={meeting_external_uid}"
        "&meeting_uid={meeting_external_uid}"
        "&fullobjects=True"
        # by default fullobjects return everything, here we include nothing
        # so by default only base data (id, title, UID, ...) are returned
        "&include_all=false"
        # field required by application
        "&metadata_fields=itemNumber"
        # field required by application
        "&metadata_fields=groupsInCharge"
        # field required by application, will be "category" or "classifier"
        "&metadata_fields={delib_category_field}"
        "{category_filter}"
        "{representatives_filter}"
        "{item_uids_filter}".format(
            plonemeeting_url=institution.plonemeeting_url.rstrip("/"),
            type=PLONEMEETING_API_ITEM_TYPE,
            meeting_config_id=institution.meeting_config_id,
            meeting_external_uid=meeting_external_uid,
            delib_category_field=institution.delib_category_field,
            category_filter=category_filter,
            representatives_filter=representatives_filter,
            item_uids_filter=item_uids_filter
        )
    )

    if with_additional_published_items_query_string:
        url += institution.additional_published_items_query_string
    return url


def get_api_url_for_meeting_item(institution, meeting_item_uids):
    if not institution.plonemeeting_url or not institution.meeting_config_id:
        return
    category_filter = _get_category_filter_url(institution)
    representatives_filter = _get_representatives_filter_url(institution)
    url = (
        "{0}/@search?"
        "type={1}"
        "&sort_on=getItemNumber"
        "&privacy=public"
        "&privacy=public_heading"
        "&b_size=9999"
        "&additional_values=formatted_itemNumber"
        "&config_id={2}"
        "&uid={3}"
        "&meeting_uid={3}"
        "&fullobjects=True"
        # by default fullobjects return everything, here we include nothing
        # so by default only base data (id, title, UID, ...) are returned
        "&include_all=false"
        # field required by application
        "&metadata_fields=itemNumber"
        # field required by application
        "&metadata_fields=groupsInCharge"
        # field required by application, will be "category" or "classifier"
        "&metadata_fields={4}"
        "{5}"
        "{6}"
        "{7}".format(
            institution.plonemeeting_url.rstrip("/"),
            PLONEMEETING_API_ITEM_TYPE,
            institution.meeting_config_id,
            "&uid={3}".join(meeting_item_uids),
            institution.delib_category_field,
            institution.additional_published_items_query_string,
            category_filter,
            representatives_filter
        )
    )
    return url


def get_api_url_for_categories(institution, delib_config_category_field):
    if institution.plonemeeting_url and institution.meeting_config_id:
        url = "{plonemeeting_url}/@config?config_id={meeting_config_id}&extra_include={delib_category_field}".format(
            plonemeeting_url=institution.plonemeeting_url.rstrip("/"),
            meeting_config_id=institution.meeting_config_id,
            delib_category_field=delib_config_category_field
        )
        return url
    else:
        return


def create_faceted_folder(container, title, id):
    folder = api.content.create(
        type="Folder", title=title, container=container, id=id
    )
    subtyper = folder.restrictedTraverse("@@faceted_subtyper")
    subtyper.enable()
    return folder


def set_constrain_types(obj, portal_type_ids):
    behavior = ISelectableConstrainTypes(obj)
    behavior.setConstrainTypesMode(1)
    behavior.setImmediatelyAddableTypes(portal_type_ids)
    behavior.setLocallyAllowedTypes(portal_type_ids)


def cleanup_contents():
    portal = api.portal.get()
    for content_id in CONTENTS_TO_CLEAN:
        content = getattr(portal, content_id, None)
        if content:
            api.content.delete(content)


def remove_left_portlets():
    remove_portlets("plone.leftcolumn")


def remove_right_portlets():
    remove_portlets("plone.rightcolumn")


def remove_portlets(column):
    portal = api.portal.get()
    manager = getUtility(IPortletManager, name=column, context=portal)
    assignments = getMultiAdapter((portal, manager), IPortletAssignmentMapping)
    for portlet in assignments:
        del assignments[portlet]


def format_meeting_date_and_state(date, state_id, format="%d %B %Y (%H:%M)", lang=None):
    """
    Format the meeting date while managing translations of months and weekdays
    :param date: Datetime reprensenting the meeting date
    :param format: format of the returning date. See strftime for directives.
    """
    MONTHS_IDS = {
        1: "month_jan",
        2: "month_feb",
        3: "month_mar",
        4: "month_apr",
        5: "month_may",
        6: "month_jun",
        7: "month_jul",
        8: "month_aug",
        9: "month_sep",
        10: "month_oct",
        11: "month_nov",
        12: "month_dec",
    }
    WEEKDAYS_IDS = {
        0: "weekday_mon",
        1: "weekday_tue",
        2: "weekday_wed",
        3: "weekday_thu",
        4: "weekday_fri",
        5: "weekday_sat",
        6: "weekday_sun",
    }
    format = format.replace("%B", "[month]").replace("%A", "[weekday]")
    date_str = safe_unicode(date.strftime(format))

    if not lang:
        lang = api.portal.get_tool("portal_languages").getDefaultLanguage()

    # in some cases month are not properly translated using sublocales
    lang = lang.split("-")[0]

    if u"[month]" in date_str:
        month = translate(
            MONTHS_IDS[date.month], domain="plonelocales", target_language=lang
        )
        date_str = date_str.replace("[month]", month)

    if u"[weekday]" in date_str:
        weekday = translate(
            WEEKDAYS_IDS[date.weekday()], domain="plonelocales", target_language=lang
        )
        date_str = date_str.replace(u"[weekday]", weekday)

    state = translate(_(state_id), target_language=lang)
    return "{0} — {1}".format(date_str, state)


def get_global_category(institution, item_local_category):
    global_category = ""
    if not institution.categories_mappings:
        return item_local_category
    for mapping in institution.categories_mappings:
        if mapping["local_category_id"] == item_local_category:
            return mapping["global_category_id"]
    if not global_category:
        return item_local_category


def redirect(request, to):
    """Redirect the given p_request to p_to which is an URL str"""
    request.response.redirect(to)


def redirect_back(request):
    """Redirect back"""
    redirect(request, request.get("HTTP_REFERER"))
