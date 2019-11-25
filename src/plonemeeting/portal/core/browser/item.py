# -*- coding: utf-8 -*-

from plone import api
from plone.dexterity.browser.view import DefaultView
from zope.component._api import getMultiAdapter


class ItemView(DefaultView):
    """
    """

    def get_files(self):
        brains = api.content.find(portal_type="File", context=self.context)
        return brains

    def get_global_category(self):
        item_local_category = self.context.category
        utils_view = getMultiAdapter((self.context, self.request), name='utils_view')
        institution = self.context.aq_parent.aq_parent
        global_category = ''
        for mapping in institution.categories_mappings:
            if mapping['local_category_id'] == item_local_category:
                global_category = mapping['global_category_id']
                break
        if not global_category:
            return item_local_category
        global_category_label = utils_view.get_categories_mappings_value(global_category)
        return global_category_label if global_category_label else global_category
