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
from plonemeeting.portal.core.config import PLONEMEETING_API_MEETINGS_VIEW
from plonemeeting.portal.core.config import PLONEMEETING_API_MEETING_ITEMS_VIEW


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
    url = "{0}/{1}?getConfigId={2}".format(
        institution.plonemeeting_url.rstrip("/"),
        PLONEMEETING_API_MEETINGS_VIEW,
        institution.meeting_config_id,
    )
    if meeting_UID:
        url = "{0}&UID={1}&fullobjects=True&b_size=9999".format(url, meeting_UID)
    else:
        url = "{0}{1}".format(url, institution.additional_meeting_query_string_for_list)
    return url


def get_api_url_for_meeting_items(institution, meeting_UID):
    if not institution.plonemeeting_url or not institution.meeting_config_id:
        return
    url = "{0}/{1}?sort_on=getItemNumber&privacy=public&privacy=public_heading&b_size=9999" \
        "&getConfigId={2}&linkedMeetingUID={3}&fullobjects=True{4}".format(
            institution.plonemeeting_url.rstrip("/"),
            PLONEMEETING_API_MEETING_ITEMS_VIEW,
            institution.meeting_config_id,
            meeting_UID,
            institution.additional_published_items_query_string,
        )
    return url


def create_faceted_folder(container, title, id=None):
    if id:
        folder = api.content.create(
            type="Folder", title=title, container=container, id=id
        )
    else:
        folder = api.content.create(type="Folder", title=title, container=container)
    api.content.transition(folder, to_state="published")
    subtyper = folder.restrictedTraverse("@@faceted_subtyper")
    subtyper.enable()
    set_constrain_types(folder, [])
    return folder


def set_constrain_types(obj, list_contraint):
    behavior = ISelectableConstrainTypes(obj)
    behavior.setConstrainTypesMode(1)
    behavior.setImmediatelyAddableTypes(list_contraint)
    behavior.setLocallyAllowedTypes(list_contraint)


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
