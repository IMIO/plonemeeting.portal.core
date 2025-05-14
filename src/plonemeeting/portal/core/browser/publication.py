from imio.helpers.workflow import get_state_infos
from imio.pyutils.utils import sort_by_indexes
from plone import api
from plone.app.content.browser.content_status_modify import ContentStatusModifyView
from plone.dexterity.browser.add import DefaultAddForm
from plone.dexterity.browser.add import DefaultAddView
from plone.dexterity.browser.edit import DefaultEditForm
from plone.dexterity.browser.view import DefaultView
from plonemeeting.portal.core import _
from Products.CMFCore.permissions import ModifyPortalContent
from Products.CMFCore.utils import _checkPermission, getToolByName

FIELDSETS_ORDER = ["authority", "dates", "timestamp", "categorization", "settings"]
ADMIN_FIELDSETS = ["settings"]

class AddForm(DefaultAddForm):
    """Override to reorder and filter out fieldsets."""

    def updateFields(self):
        super(AddForm, self).updateFields()
        indexes = [FIELDSETS_ORDER.index(group.__name__) for group in self.groups]
        groups = sort_by_indexes(self.groups, indexes)
        pm = getToolByName(self.context, 'portal_membership')
        if not pm.checkPermission('Manage portal', self.context):
            groups = filter(lambda g: g.__name__ not in ADMIN_FIELDSETS, groups)
        self.groups = groups


class PublicationAdd(DefaultAddView):

    form = AddForm


class EditForm(DefaultEditForm):
    """Override to reorder and filter out fieldsets."""

    def updateFields(self):
        super(EditForm, self).updateFields()
        indexes = [FIELDSETS_ORDER.index(group.__name__) for group in self.groups]
        groups = sort_by_indexes(self.groups, indexes)
        pm = getToolByName(self.context, 'portal_membership')
        if not pm.checkPermission('Manage portal', self.context):
            groups = filter(lambda g: g.__name__ not in ADMIN_FIELDSETS, groups)
        self.groups = groups


class PublicationView(DefaultView):
    """
    """

    def __call__(self):
        if api.content.get_state(self.context) == 'private' and \
           _checkPermission(ModifyPortalContent, self.context) and \
           self.context.enable_timestamping is False:
            api.portal.show_message(
                _("Timestamping is disabled for this element!"),
                request=self.request,
                type="warning")
        return super(PublicationView, self).__call__()

    def get_effective_date(self):
        return self.context.effective_date.strftime('%d/%m/%Y à %H:%M') \
            if self.context.effective_date else "-"

    def get_expiration_date(self):
        return self.context.expiration_date.strftime('%d/%m/%Y à %H:%M') \
            if self.context.expiration_date else "-"

    def get_decision_date(self):
        return self.context.decision_date.strftime('%d/%m/%Y') \
            if self.context.decision_date else "-"

    def get_authority_date(self):
        return self.context.authority_date.strftime('%d/%m/%Y') \
            if self.context.authority_date else "-"

    def get_expired_authority_date(self):
        return self.context.expired_authority_date.strftime('%d/%m/%Y') \
            if self.context.expired_authority_date else "-"

    def get_entry_date(self):
        return self.context.entry_date.strftime('%d/%m/%Y') \
            if self.context.entry_date else "-"

    def get_state_title(self):
        return get_state_infos(self.context)['state_title']


class PublicationContentStatusModifyView(ContentStatusModifyView):
    """Override to not set a publication date automatically."""

    def editContent(self, obj, effective, expiry):
        """Override to bypass setting effective_date and
           expiration_date upon any workflow transition."""
        return
