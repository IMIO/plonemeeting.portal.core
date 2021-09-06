# -*- coding: utf-8 -*-
from plone import api
from plone.app.textfield.value import IRichTextValue
from plone.portlets.interfaces import IPortletAssignmentMapping
from plone.portlets.interfaces import IPortletManager
from plonemeeting.portal.core import _
from plonemeeting.portal.core.config import CONTENTS_TO_CLEAN
from plonemeeting.portal.core.config import PLONEMEETING_API_ITEM_TYPE
from plonemeeting.portal.core.config import PLONEMEETING_API_MEETING_TYPE
from plonemeeting.portal.core.config import REPRESENTATIVE_IA_DELIB_FIELD
from Products.CMFPlone.interfaces.constrains import ISelectableConstrainTypes
from Products.CMFPlone.utils import safe_unicode
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.globalrequest import getRequest
from zope.i18n import translate
from zope.interface import provider
from zope.schema.interfaces import IContextAwareDefaultFactory


def format_institution_managers_group_id(institution):
    return "{0}-institution_managers".format(institution.id)


def get_text_from_richtext(field):
    if IRichTextValue.providedBy(field):
        transforms = api.portal.get_tool("portal_transforms")
        raw = safe_unicode(field.raw)
        text = (
            transforms.convertTo("text/plain", raw, mimetype=field.mimeType)
            .getData()
            .strip()
        )
        return safe_unicode(text)


def default_translator(msgstring, **replacements):
    @provider(IContextAwareDefaultFactory)
    def context_provider(context):
        value = translate(msgstring, context=getRequest())
        if replacements:
            value = value.format(**replacements)
        return value

    return context_provider


def get_api_url_for_meetings(institution, meeting_UID=None):
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
    if meeting_UID:
        url = "{0}&UID={1}" \
            "&fullobjects=True" \
            "&include_all=false" \
            "&metadata_fields=date" \
            "&b_size=9999".format(url, meeting_UID)
    else:
        url += _datagrid_to_url_param(institution.meeting_filter_query)
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


def get_api_url_for_annexes(institution, item_json_id):
    url = "{0}/@annexes?publishable=true" \
        "&fullobjects" \
        "&include_all=false" \
        "&metadata_fields=file" \
        "&metadata_fields=content_category" \
        "&additional_values=category_title" \
        "&additional_values=subcategory_title".format(item_json_id)
    return url


def _datagrid_to_url_param(values):
    res = ''
    for dict_value in values:
        res += '&{parameter}={value}'.format(parameter=dict_value['parameter'], value=dict_value['value'])
    return res


def get_api_url_for_meeting_items(institution, meeting_UID):
    if not institution.plonemeeting_url or not institution.meeting_config_id:
        return
    category_filter = _get_category_filter_url(institution)
    representatives_filter = _get_representatives_filter_url(institution)

    item_filter_query = _datagrid_to_url_param(institution.item_filter_query)
    item_content_query = _datagrid_to_url_param(institution.item_content_query)
    # XXX linkedMeetingUID/meeting_uid compatibility, index was renamed to meeting_uid
    url = (
        "{0}/@search?"
        "type={1}"
        "&sort_on=getItemNumber"
        "&privacy=public"
        "&privacy=public_heading"
        "&b_size=9999"
        "&additional_values=formatted_itemNumber"
        "&config_id={2}"
        "&linkedMeetingUID={3}"
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
        "{7}"
        "{8}".format(
            institution.plonemeeting_url.rstrip("/"),
            PLONEMEETING_API_ITEM_TYPE,
            institution.meeting_config_id,
            meeting_UID,
            institution.delib_category_field,
            item_filter_query,
            item_content_query,
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


def get_api_url_for_representatives(institution):
    if institution.plonemeeting_url and institution.meeting_config_id:
        url = "{plonemeeting_url}/@config?config_id={meeting_config_id}&extra_include={representative}".format(
            plonemeeting_url=institution.plonemeeting_url.rstrip("/"),
            meeting_config_id=institution.meeting_config_id,
            representative=REPRESENTATIVE_IA_DELIB_FIELD
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
