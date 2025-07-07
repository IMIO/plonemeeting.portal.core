from collective.timestamp.interfaces import ITimeStamper
from imio.helpers.workflow import get_state_infos
from imio.pyutils.utils import sort_by_indexes
from plone import api
from plone.app.content.browser.content_status_modify import ContentStatusModifyView
from plone.dexterity.browser.add import DefaultAddForm
from plone.dexterity.browser.add import DefaultAddView
from plone.dexterity.browser.edit import DefaultEditForm
from plone.dexterity.browser.view import DefaultView
from plone.dexterity.events import EditCancelledEvent
from plone.dexterity.events import EditFinishedEvent
from plonemeeting.portal.core import _
from Products.CMFCore.permissions import ModifyPortalContent
from Products.CMFCore.utils import _checkPermission
from Products.CMFCore.utils import getToolByName
from Products.statusmessages.interfaces import IStatusMessage
from z3c.form import button
from zope.event import notify


FIELDSETS_ORDER = ["authority", "dates", "timestamp", "categorization", "settings"]
ADMIN_FIELDSETS = ["settings"]


class AddForm(DefaultAddForm):
    """Override to reorder and filter out fieldsets."""

    def updateFields(self):
        super(AddForm, self).updateFields()
        indexes = [FIELDSETS_ORDER.index(group.__name__) for group in self.groups]
        groups = sort_by_indexes(self.groups, indexes)
        pm = getToolByName(self.context, "portal_membership")
        if not pm.checkPermission("Manage portal", self.context):
            groups = filter(lambda g: g.__name__ not in ADMIN_FIELDSETS, groups)
        self.groups = groups


class PublicationAdd(DefaultAddView):

    form = AddForm


class EditForm(DefaultEditForm):
    """Override to reorder and filter out fieldsets."""

    def render(self):
        """Override to warn about timestamped content.
        We plug ourself here to avoid displaying the warning after the submit."""
        handler = ITimeStamper(self.context)
        if handler.is_timestamped():
            IStatusMessage(self.request).addStatusMessage(
                _("msg_editing_timestamped_content"), "warning"
            )
        return super().render()

    @button.buttonAndHandler(_("Save"), name="save")
    def handleApply(self, action):
        data, errors = self.extractData()
        if api.content.get_state(self.context) in ("planned", "published") and not data.get("IPublication.effective"):
            IStatusMessage(self.request).addStatusMessage(_("msg_missing_effective_date"), "error")
            return
        super(EditForm, self).handleApply(self, action)

    @button.buttonAndHandler(_("Cancel"), name="cancel")
    def handleCancel(self, action):
        super(EditForm, self).handleCancel(self, action)

    @button.buttonAndHandler(_("Cancel"), name="cancel")
    def handleCancel(self, action):
        IStatusMessage(self.request).addStatusMessage(_("Edit cancelled"), "info")
        self.request.response.redirect(self.nextURL())
        notify(EditCancelledEvent(self.context))

    def updateFields(self):
        super(EditForm, self).updateFields()
        indexes = [FIELDSETS_ORDER.index(group.__name__) for group in self.groups]
        groups = sort_by_indexes(self.groups, indexes)
        pm = getToolByName(self.context, "portal_membership")
        if not pm.checkPermission("Manage portal", self.context):
            groups = filter(lambda g: g.__name__ not in ADMIN_FIELDSETS, groups)
        self.groups = groups


class PublicationView(DefaultView):
    """ """

    def __call__(self):
        if api.content.get_state(self.context) == "private" and _checkPermission(ModifyPortalContent, self.context):
            if self.context.enable_timestamping is False:
                api.portal.show_message(
                    _("Timestamping is disabled for this element!"), request=self.request, type="warning"
                )
            if (
                self.context.effective_date
                and self.context.effective_date.isPast()
                and self.context.enable_timestamping
            ):
                api.portal.show_message(_("effective_date_in_past_msg"), request=self.request, type="warning")
        return super(PublicationView, self).__call__()

    def get_effective_date(self):
        return self.context.effective_date.strftime("%d/%m/%Y à %H:%M") if self.context.effective_date else "-"

    def get_expiration_date(self):
        return self.context.expiration_date.strftime("%d/%m/%Y à %H:%M") if self.context.expiration_date else "-"

    def get_decision_date(self):
        return self.context.decision_date.strftime("%d/%m/%Y") if self.context.decision_date else "-"

    def get_authority_date(self):
        return self.context.authority_date.strftime("%d/%m/%Y") if self.context.authority_date else "-"

    def get_expired_authority_date(self):
        return self.context.expired_authority_date.strftime("%d/%m/%Y") if self.context.expired_authority_date else "-"

    def get_entry_date(self):
        return self.context.entry_date.strftime("%d/%m/%Y") if self.context.entry_date else "-"

    def get_state_title(self):
        return get_state_infos(self.context)["state_title"]


class PublicationContentStatusModifyView(ContentStatusModifyView):
    """Override to not set a publication date automatically."""

    def editContent(self, obj, effective, expiry):
        """Override to bypass setting effective_date and
        expiration_date upon any workflow transition."""
        return
