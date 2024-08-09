from plone import api


def published_institutions_modified_cachekey(method, self):
    """
    Institution cache key based on a list of ids and last modification date
    """
    brains = api.content.find(portal_type="Institution",
                              review_state="published",
                              sort_on='getId')
    return [brain.id + "_" + str(brain.modified) for brain in brains]

def item_meeting_modified_cachekey(method, self):
    """
    Cache key based of item's meeting modification date
    """
    return self.get_meeting().modified
