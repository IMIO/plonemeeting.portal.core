# -*- coding: utf-8 -*-
from imio.migrator.utils import end_time
from plone import api
from plone.app.content.utils import json_dumps
from plone.autoform.form import AutoExtensibleForm
from plonemeeting.portal.core import _
from plonemeeting.portal.core import logger
from plonemeeting.portal.core import plone_
from plonemeeting.portal.core.content.item import IItem
from plonemeeting.portal.core.interfaces import IMeetingsFolder
from plonemeeting.portal.core.sync_utils import _call_delib_rest_api
from plonemeeting.portal.core.sync_utils import _json_date_to_datetime
from plonemeeting.portal.core.sync_utils import sync_meeting
from plonemeeting.portal.core.utils import get_api_url_for_meeting_items
from plonemeeting.portal.core.utils import get_api_url_for_meetings
from plonemeeting.portal.core.utils import get_api_url_for_presync_meeting_items
from plonemeeting.portal.core.utils import redirect
from Products.Five import BrowserView
from z3c.form import button
from z3c.form.contentprovider import ContentProviders
from z3c.form.form import Form
from z3c.form.interfaces import IFieldsAndContentProvidersForm
from zope import schema
from zope.browserpage.viewpagetemplatefile import ViewPageTemplateFile
from zope.contentprovider.provider import ContentProviderBase
from zope.i18n import translate
from zope.interface import implementer
from zope.interface import Interface

import copy
import json
import requests
import time


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

    @button.buttonAndHandler(_(u"Select"))
    def handle_select(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        external_meeting_uid = data.get("meeting")
        next_form_url = (
            self.context.absolute_url() + "/@@pre_import_report_form?external_meeting_uid=" + external_meeting_uid
        )
        redirect(self.request, next_form_url)

    def update(self):
        try:
            super(ImportMeetingForm, self).update()
        except requests.exceptions.ConnectionError as err:
            self._notify_error_and_cancel(err)

    def _notify_error_and_cancel(self, err=None):
        logger.warning("Error while trying to connect to iA.Delib",
                       exc_info=err)
        api.portal.show_message(
            _("Webservice connection error !"), request=self.request,
            type="error"
        )
        self.handle_cancel(self, None)

    @button.buttonAndHandler(plone_(u"Cancel"))
    def handle_cancel(self, action):
        meeting_faceted_url = (
            self.context.absolute_url() + "/seances"
        )
        redirect(self.request, meeting_faceted_url)

    def updateActions(self):
        super().updateActions()
        self.actions["select"].addClass("context")
        self.actions["cancel"].addClass("standalone")

class ImportMeetingView(BrowserView):  # pragma: no cover
    def import_meeting(self, force=False):
        meeting = self.context
        institution = meeting.aq_parent
        _sync_meeting(institution, meeting.plonemeeting_uid, self.request,
                      force)


class SyncMeetingView(ImportMeetingView):  # pragma: no cover
    def __call__(self):
        self.import_meeting()


class ForceReimportMeetingView(ImportMeetingView):  # pragma: no cover
    def __call__(self):
        self.import_meeting(force=True)


class ItemsContentProvider(ContentProviderBase):
    template = ViewPageTemplateFile("templates/items_datatable.pt")

    def __init__(self, context, request, view):
        super(ItemsContentProvider, self).__init__(context, request, view)
        self.parent = view
        self.meeting_uid = None

    def get_items(self):
        if hasattr(self.parent, "api_response_data"):
            return self.parent.api_response_data["items"]

    def to_json(self, value):
        return json_dumps(value)

    def render(self, *args, **kwargs):
        datatable_config = {
            "paging": False,
            "columnDefs": [
                {"orderable": False, "width": "30px", "targets": 0},
                {"orderable": False, "width": "50px", "targets": 3},
                {"orderable": False, "width": "50px", "targets": 4}

            ],
            "scrollY": "50vh",
            "autoWidth": True,
            "scrollCollapse": True,
            "order": [[1, "asc"]],
            "language": {
                "search": translate(plone_(u"Search"), context=self.request),
                "emptyTable": translate(_(u"No data available in table"),
                                        context=self.request),
                "info": translate(
                    _("Showing _START_ to _END_ of _TOTAL_ entries"),
                    context=self.request),
                "aria": {
                    "sortAscending": translate(
                        _("activate to sort column ascending"),
                        context=self.request),
                    "sortDescendintranslate": translate(
                        _("activate to sort column descending"),
                        context=self.request)
                },
            },
        }
        return self.template(datatable_config=json.dumps(datatable_config))


@implementer(IFieldsAndContentProvidersForm)
class PreSyncReportForm(Form):
    """"""

    label = _(u"Meeting pre sync form")
    description = _(u"Choose items you want to sync/import in the portal.")

    contentProviders = ContentProviders()
    contentProviders["items"] = ItemsContentProvider
    contentProviders["items"].position = 0

    def __call__(self):
        self.utils_view = self.context.restrictedTraverse("@@utils_view")
        self.external_meeting_uid = self.context.plonemeeting_uid
        self.is_syncing = True
        self.institution = self.utils_view.get_current_institution()
        self.items = self.context.get_items()
        self.meeting_title = self.context.Title()
        self.api_response_data = _fetch_preview_items(self.context,
                                                      self.external_meeting_uid)
        self.api_response_data = self._reconcile_items(self.api_response_data,
                                                       self.items)

        return super(PreSyncReportForm, self).__call__()

    @button.buttonAndHandler(_(u"Sync"))
    def handle_sync(self, action):
        form = self.request.form
        checked_item_uids = self._extract_checked_items(form)
        _sync_meeting(
            self.institution,
            self.external_meeting_uid,
            self.request,
            item_external_uids=checked_item_uids,
        )

    @button.buttonAndHandler(_(u"Force"))
    def handle_force_sync(self, action):
        form = self.request.form
        checked_item_uids = self._extract_checked_items(form)
        _sync_meeting(
            self.institution,
            self.external_meeting_uid,
            self.request,
            item_external_uids=checked_item_uids,
            force=True
        )

    @button.buttonAndHandler(_(u"Delete"))
    def handle_delete(self, action):
        form = self.request.form
        checked_item_uids = self._extract_checked_items(form)
        deleted_ids = []
        for item in self.context.objectValues():
            if IItem.providedBy(
                item) and item.plonemeeting_uid in checked_item_uids:
                deleted_ids.append(item.id)
        if len(deleted_ids) > 0:
            self.context.manage_delObjects(deleted_ids)

    def updateActions(self):
        super().updateActions()
        self.actions["sync"].addClass("context")
        self.actions["force"].addClass("destructive")
        self.actions["delete"].addClass("destructive")
        self.actions["cancel"].addClass("standalone")

    @button.buttonAndHandler(_(u"Cancel"))
    def handle_cancel(self, action):
        """"""
        meeting_faceted_url = (
            self.institution.absolute_url() + "/seances#seance=" + self.context.UID()
        )
        redirect(self.request, meeting_faceted_url)

    def _reconcile_items(self, api_items, local_items):
        reconciled = copy.deepcopy(api_items)
        local_items_by_plonemeeting_uid = {item.plonemeeting_uid: item for item
                                           in local_items}

        for item in reconciled["items"]:
            api_annexes = item.get("extra_include_annexes", [])
            if item["UID"] in local_items_by_plonemeeting_uid.keys():
                local_item = local_items_by_plonemeeting_uid[item["UID"]]
                plonemeeting_last_modified = _json_date_to_datetime(
                    item["modified"])
                item[
                    "local_last_modified"] = local_item.plonemeeting_last_modified.isoformat()
                item["modified"] = plonemeeting_last_modified.isoformat()
                if local_item.plonemeeting_last_modified == plonemeeting_last_modified \
                    and local_item.number == item["formatted_itemNumber"]:
                        item["status"] = "unchanged"
                        item["status_label"] = _(u"Unchanged")
                else:
                    item["status"] = "modified"
                    item["status_label"] = _(u"Modified")
                item["annexes_status"] = self._reconcile_annexes(
                    api_annexes, local_item.objectValues()
                )
                local_items_by_plonemeeting_uid.pop(item["UID"])
            else:
                item["local_last_modified"] = "-"
                item["status"] = "added"
                item["status_label"] = _(u"Added")
                item["annexes_status"] = {}
                if api_annexes:
                    item["annexes_status"] = {
                        "added": {
                            "count": len(api_annexes),
                            "titles": [annex["title"] for annex in api_annexes],
                        },
                    }

        for uid, local_item in local_items_by_plonemeeting_uid.items():
            annexes_status = {}
            annexes_count = local_item.objectCount()
            if annexes_count:
                annexes_status["removed"] = {
                    "count": annexes_count,
                    "label": _(u"Removed"),
                    "titles": [annex.Title() for annex in
                               local_item.objectValues()],
                }
            reconciled["items"].append(
                {
                    "UID": local_item.plonemeeting_uid,
                    "title": local_item.title,
                    "formatted_itemNumber": local_item.number,
                    "modified": "-",
                    "local_last_modified": local_item.plonemeeting_last_modified.isoformat(),
                    "category": {
                        "title": "-"
                    },
                    "representatives_in_charge": "-",
                    "status": "removed",
                    "status_label": _(u"Removed"),
                    "annexes_status": annexes_status
                },
            )
        return reconciled

    def _reconcile_annexes(self, api_annexes, local_annexes):
        annexes_status = {
            "added": {"count": 0,
                      "label": translate(_(u"Added"), context=self.request),
                      "titles": []},
            "unchanged": {"count": 0, "label": translate(_(u"Unchanged"),
                                                         context=self.request),
                          "titles": []},
            "modified": {"count": 0, "label": translate(_(u"Modified"),
                                                        context=self.request),
                         "titles": []},
            "removed": {"count": 0,
                        "label": translate(_(u"Removed"), context=self.request),
                        "titles": []},
        }
        local_annexes_by_plonemeeting_uid = {
            annexe.plonemeeting_uid: annexe for annexe in local_annexes
        }

        for api_annexe in api_annexes:
            if api_annexe["UID"] not in local_annexes_by_plonemeeting_uid.keys():
                annexes_status["added"]["count"] += 1
                annexes_status["added"]["titles"].append(api_annexe["title"])
            else:
                local_annexe = local_annexes_by_plonemeeting_uid[
                    api_annexe["UID"]]
                api_annexe_last_modified = _json_date_to_datetime(
                    api_annexe["modified"])

                if api_annexe_last_modified == local_annexe.plonemeeting_last_modified:
                    annexes_status["unchanged"]["count"] += 1
                    annexes_status["unchanged"]["titles"].append(
                        api_annexe["title"])
                else:
                    annexes_status["modified"]["count"] += 1
                    annexes_status["modified"]["titles"].append(
                        api_annexe["title"])
                local_annexes_by_plonemeeting_uid.pop(api_annexe["UID"])

        for local_annexe in local_annexes_by_plonemeeting_uid.values():
            annexes_status["removed"]["count"] += 1
            annexes_status["removed"]["titles"].append(local_annexe.Title())

        # Avoid 'RuntimeError: dictionary changed size during iteration'
        statuses = list(annexes_status.keys())

        for status in statuses:
            if annexes_status[status]["count"] == 0:
                annexes_status.pop(status)

        return annexes_status

    def _fetch_preview_items(self, meeting_external_uid):
        url = get_api_url_for_meeting_items(
            self.context, meeting_external_uid=meeting_external_uid
        )
        response = _call_delib_rest_api(url, self.context)
        self.api_response_data = json.loads(response.text)

    @staticmethod
    def _extract_checked_items(form):
        checked_item_uids = []
        for inputs in form.keys():
            if inputs.startswith("item_uid"):
                checked_item_uids.append(inputs.split("__")[1])
        return checked_item_uids


@implementer(IFieldsAndContentProvidersForm)
class PreImportReportForm(Form):
    """"""

    label = _(u"Meeting pre import form")
    description = _(u"Choose items you want to import in the portal.")

    ignoreContext = True
    contentProviders = ContentProviders()
    contentProviders["items"] = ItemsContentProvider
    contentProviders["items"].position = 0

    def __call__(self):
        self.external_meeting_uid = self.request.form["external_meeting_uid"]
        self.is_syncing = False
        self.institution = self.context
        self.meeting_title = _call_delib_rest_api(
            get_api_url_for_meetings(self.institution,
                                     self.external_meeting_uid),
            self.institution,
        ).json()["items"][0]["title"]
        self.api_response_data = _fetch_preview_items(self.context,
                                                      self.external_meeting_uid)
        return super(PreImportReportForm, self).__call__()

    @button.buttonAndHandler(_(u"Import"))
    def handle_import(self, action):
        form = self.request.form
        checked_item_uids = []
        for inputs in form.keys():
            if inputs.startswith("item_uid"):
                checked_item_uids.append(inputs.split("__")[1])
        _sync_meeting(
            self.institution,
            self.external_meeting_uid,
            self.request,
            item_external_uids=checked_item_uids,
        )

    @button.buttonAndHandler(_(u"Cancel"))
    def handle_cancel(self, action):
        redirect(self.request,
                 self.context.absolute_url() + "/@@import_meeting")

    def updateActions(self):
        super().updateActions()
        self.actions["import"].addClass("context")
        self.actions["cancel"].addClass("standalone")


def _fetch_preview_items(context, meeting_external_uid):
    url = get_api_url_for_presync_meeting_items(context,
                                                meeting_external_uid=meeting_external_uid)
    response = _call_delib_rest_api(url, context)
    return json.loads(response.text)


def _sync_meeting(
    institution, meeting_uid, request, force=False, item_external_uids=[]
):  # pragma: no cover
    try:
        start_time = time.time()
        logger.info("SYNC starting...")
        status, new_meeting_uid = sync_meeting(
            institution, meeting_uid, force, item_external_uids
        )
        if new_meeting_uid:
            brains = api.content.find(
                context=institution,
                object_provides=IMeetingsFolder.__identifier__
            )

            if brains:
                request.response.redirect(
                    "{0}#seance={1}".format(brains[0].getURL(), new_meeting_uid)
                )
                api.portal.show_message(message=status, request=request,
                                        type="info")
        else:
            api.portal.show_message(message=status, request=request,
                                    type="error")
        logger.info(end_time(start_time, "SYNC PROCESSED IN "))
    except ValueError as error:
        api.portal.show_message(message=error.args[0], request=request,
                                type="error")
