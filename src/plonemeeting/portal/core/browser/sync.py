# -*- coding: utf-8 -*-
import json

from imio.migrator.utils import end_time
from Products.Five import BrowserView
from plone import api
from plone.app.content.utils import json_dumps
from plone.autoform.form import AutoExtensibleForm
from plonemeeting.portal.core.sync_utils import sync_meeting, _call_delib_rest_api
from plonemeeting.portal.core.utils import get_api_url_for_meeting_items
from z3c.form import button
from z3c.form.contentprovider import ContentProviders
from z3c.form.form import Form
from z3c.form.interfaces import IFieldsAndContentProvidersForm
from zope import schema
from zope.browserpage.viewpagetemplatefile import ViewPageTemplateFile
from zope.contentprovider.provider import ContentProviderBase
from zope.interface import Interface, implementer

import time

from plonemeeting.portal.core import _
from plonemeeting.portal.core import logger
from plonemeeting.portal.core.interfaces import IMeetingsFolder


class IImportMeetingForm(Interface):
    """
    """

    meeting = schema.Choice(
        title=_(u"Meeting"), vocabulary="plonemeeting.portal.vocabularies.remote_meetings", required=True,
    )


class ImportMeetingForm(AutoExtensibleForm, Form):

    """
    """

    schema = IImportMeetingForm
    ignoreContext = True

    label = _(u"Meeting import form")
    description = _(u"Choose the meeting you want to import in the portal.")

    @button.buttonAndHandler(_(u"Sélectionner"))
    def handle_select(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        external_meeting_uid = data.get("meeting")
        self.request.response.redirect(
            self.context.absolute_url() + "/@@presync_report_form?external_meeting_uid=" + external_meeting_uid
        )

    # _sync_meeting(institution, meeting_uid, self.request)

    @button.buttonAndHandler(_(u"Cancel"))
    def handle_cancel(self, action):
        """
        """
        self.request.response.redirect(self.request.get("HTTP_REFERER"))


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


class ItemsContentProvider(ContentProviderBase):
    template = ViewPageTemplateFile("templates/items_datatable.pt")

    def __init__(self, context, request, view):
        super(ItemsContentProvider, self).__init__(context, request, view)
        self.__parent__ = view
        self.meeting_uid = None

    def get_datatables_config(self):
        # FIXME
        return json_dumps(
            {
                "paging": True,
                "language": {
                    "processing": "Traitement en cours...",
                    "search": "Rechercher&nbsp;:",
                    "lengthMenu": "Afficher _MENU_ &eacute;l&eacute;ments",
                    "info": "Affichage de l'&eacute;lement _START_ &agrave; _END_ sur _TOTAL_ &eacute;l&eacute;ments",
                    "infoEmpty": "Affichage de l'&eacute;lement 0 &agrave; 0 sur 0 &eacute;l&eacute;ments",
                    "infoFiltered": "(filtr&eacute; de _MAX_ &eacute;l&eacute;ments au total)",
                    "infoPostFix": "",
                    "loadingRecords": "Chargement en cours...",
                    "zeroRecords": "Aucun &eacute;l&eacute;ment &agrave; afficher",
                    "emptyTable": "Aucune donnée disponible dans le tableau",
                    "paginate": {
                        "first": "Premier",
                        "previous": "Pr&eacute;c&eacute;dent",
                        "next": "Suivant",
                        "last": "Dernier",
                    },
                    "aria": {
                        "sortAscending": ": activer pour trier la colonne par ordre croissant",
                        "sortDescending": ": activer pour trier la colonne par ordre décroissant",
                    },
                },
            }
        )

    def get_items(self):
        return self.__parent__.form.json_items

    def render(self, *args, **kwargs):
        # self.contentProviders['items'].factory.meeting_uid = data.get("meeting")
        return self.template()


@implementer(IFieldsAndContentProvidersForm)
class PreSyncReportForm(Form):
    """
    """

    label = _(u"Meeting pre sync form")
    description = _(u"Choose items you want to sync/import in the portal.")

    ignoreContext = True
    contentProviders = ContentProviders()
    contentProviders["items"] = ItemsContentProvider
    contentProviders["items"].position = 0

    def __call__(self):
        if "external_meeting_uid" in self.request.form:
            external_meeting_uid = self.request.form["external_meeting_uid"]
        self._fetch_preview_items(external_meeting_uid)
        return super(PreSyncReportForm, self).__call__()

    @button.buttonAndHandler(_(u"Import"))
    def handle_apply(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

    @button.buttonAndHandler(_(u"Cancel"))
    def handle_cancel(self, action):
        """
        """
        self.request.response.redirect(self.request.get("HTTP_REFERER"))

    def _fetch_preview_items(self, meeting_external_uid):
        url = get_api_url_for_meeting_items(self.context, meeting_external_uid=meeting_external_uid)
        response = _call_delib_rest_api(url, self.context)
        self.json_items = json.loads(response.text)["items"]


def _sync_meeting(institution, meeting_uid, request, force=False):  # pragma: no cover
    try:
        start_time = time.time()
        logger.info("SYNC starting...")
        status, new_meeting_uid = sync_meeting(institution, meeting_uid, force)
        if new_meeting_uid:
            brains = api.content.find(context=institution, object_provides=IMeetingsFolder.__identifier__)

            if brains:
                request.response.redirect("{0}#seance={1}".format(brains[0].getURL(), new_meeting_uid))
                api.portal.show_message(message=status, request=request, type="info")
        else:
            api.portal.show_message(message=status, request=request, type="error")
        logger.info(end_time(start_time, "SYNC PROCESSED IN "))
    except ValueError as error:
        api.portal.show_message(message=error.args[0], request=request, type="error")
