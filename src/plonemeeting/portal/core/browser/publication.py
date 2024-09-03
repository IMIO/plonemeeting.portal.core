from DateTime import DateTime
from imio.helpers.workflow import get_state_infos
from plone import api
from plone.app.content.browser.content_status_modify import ContentStatusModifyView
from plone.dexterity.browser.view import DefaultView
from Products.CMFCore.permissions import ModifyPortalContent
from Products.CMFCore.utils import _checkPermission


class PublicationView(DefaultView):
    """
    """

    def __call__(self):
        if api.content.get_state(self.context) == 'private' and \
           _checkPermission(ModifyPortalContent, self.context) and \
           self.context.effective_date and self.context.effective_date < DateTime():
            api.portal.show_message(
                "An effective date is defined in the past, "
                "you can not publish or plan this Publication!",
                request=self.request,
                type="warning")
        return super(PublicationView, self).__call__()

    def get_effective_date(self):
        return self.context.effective_date.strftime('%d/%m/%Y à %H:%M') \
            if self.context.effective_date else "-"

    def get_decision_date(self):
        return self.context.decision_date.strftime('%d/%m/%Y') \
            if self.context.decision_date else "-"

    def get_authority_date(self):
        return self.context.authority_date.strftime('%d/%m/%Y') \
            if self.context.authority_date else "-"

    def get_state_title(self):
        return get_state_infos(self.context)['state_title']


class PublicationContentStatusModifyView(ContentStatusModifyView):
    """Override to not set a publication date automatically."""

    def editContent(self, obj, effective, expiry):
        """Override to bypass setting effective_date and
           expiration_date upon any workflow transition."""
        return
