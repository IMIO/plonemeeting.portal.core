from plone import api


def published_institutions_modified_cachekey(method, self):
    """
    Institution cache key based on a list of ids and last modification date
    """
    brains = api.content.find(portal_type="Institution",
                              review_state="published",
                              sort_on='getId')
    return [brain.id + "_" + str(brain.modified) for brain in brains]

def meeting_modified_cachekey(method, self):
    """
    Cache key based of item's meeting modification date
    """
    return str(self.get_meeting().modified)

def item_next_prev_infos_cachekey(method, self):
    """
    Cache key for an item's next/previous infos. The result depends on the item being viewed,
    so the item id must be part of the key.
    """
    return self.context.getId() + "_" + str(self.get_meeting().modified)
