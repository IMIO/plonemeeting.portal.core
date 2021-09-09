# -*- coding: utf-8 -*-
import json

from Products.Five.browser import BrowserView
from plone import api


class HomePageView(BrowserView):

    def get_json_institutions(self):
        portal = api.portal.get()



        institutions = {obj.id: {
            "title": obj.Title(),
            "URL": obj.absolute_url(),
#            "city_logo": obj.get_city_logo().absolute_url()
        } for obj in portal.objectValues() if obj.portal_type == "Institution"}
        return json.dumps(institutions)
