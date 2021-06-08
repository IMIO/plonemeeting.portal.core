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
