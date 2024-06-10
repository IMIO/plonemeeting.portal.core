from plone.app.dexterity.behaviors.nextprevious import NextPreviousBase


class NextPrevPortalType(NextPreviousBase):
    """
    Based on plone.app.dexterity.behaviors.nextprevious.NextPreviousBase
    to get the next and previous item in the container with a specific portal_type
    """

    def __init__(self, context, portal_type):
        self.portal_type = portal_type
        super().__init__(context)

    def getNextItem(self, obj):
        """return info about the next item in the container"""
        if not self.order:
            return None
        pos = self.context.getObjectPosition(obj.getId())
        if pos is None:
            return None
        for oid in self.order[pos + 1 :]:
            obj = self.context[oid]
            if obj.portal_type != self.portal_type:
                continue
            data = self.getData(obj)
            if data:
                return data

    def getPreviousItem(self, obj):
        """return info about the previous item in the container"""
        if not self.order:
            return None
        order_reversed = list(reversed(self.order))
        pos = order_reversed.index(obj.getId())
        for oid in order_reversed[pos + 1 :]:
            obj = self.context[oid]
            if obj.portal_type != self.portal_type:
                continue
            data = self.getData(obj)
            if data:
                return data
