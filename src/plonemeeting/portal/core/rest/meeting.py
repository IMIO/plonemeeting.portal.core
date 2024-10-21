from Acquisition import aq_parent
from plone.restapi.interfaces import IJsonCompatible
from plonemeeting.portal.core.rest.base import PublicAPIView
from plonemeeting.portal.core.rest.interfaces import IItemSerializeToJson
from Products.CMFCore.utils import getToolByName
from zope.component import queryMultiAdapter


class MeetingAgendaAPIView(PublicAPIView):
    def reply(self):
        if self.request.method == "GET":
            res = []
            items = self.context.get_items(objects=True)
            for item in items:
                serializer = queryMultiAdapter((item, self.request), IItemSerializeToJson)
                res.append(serializer(fieldnames=["formatted_title", "number"]))
            return IJsonCompatible(res)
