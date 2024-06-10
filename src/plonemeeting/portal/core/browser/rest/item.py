from Acquisition import aq_parent
from plone.restapi.interfaces import IJsonCompatible
from plone.restapi.services import Service
from plonemeeting.portal.core.browser.rest.base import PublicAPIView


class ItemNavigationAPIView(PublicAPIView):
    def reply(self):
        if self.request.method == "GET":
            item = self.context
            meeting = aq_parent(item)

            return IJsonCompatible(
                {
                    "current": item.sortable_number,
                    "count": 250,
                    "next": "https//www.google.com",
                    "previous": "https//www.google.com"
                }
            )
