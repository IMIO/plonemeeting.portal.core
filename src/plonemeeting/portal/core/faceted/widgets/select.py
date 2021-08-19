# -*- coding: utf-8 -*-

from eea.facetednavigation.widgets.select.interfaces import ISelectSchema
from eea.facetednavigation.widgets.select.widget import Widget


class ISelectMeetingSchema(ISelectSchema):
    """ """


class SelectMeetingWidget(Widget):
    """ """

    @property
    def default(self):
        """ For the "seance" criterion, we will return last value of the vocabulary
            instead default selected on the widget (by default "All")
        """
        default = super(SelectMeetingWidget, self).default or u''
        if self.data.__name__ == 'seance':
            meetings = self.vocabulary()
            if meetings:
                default = meetings[0][0]
        return default

    def count(self, brains, sequence=None):
        """For the "seance" criterion, change the count result,
           as count of "0" are disabled by view.js, change "0" to "-"
           so elements are still selectable in select box.
           Some meetings do not hold items but just some PDF files (old imported meetings).
        """
        res = super(SelectMeetingWidget, self).count(brains, sequence)
        # turn "0" count into "-" so it is ignored by view.js and not disabled
        if self.data.__name__ == 'seance':
            res = {k: v or '-' for k, v in res.items()}
        return res
