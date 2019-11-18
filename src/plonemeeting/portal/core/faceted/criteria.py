# -*- coding: utf-8 -*-

from eea.facetednavigation.criteria.handler import Criteria
from plone import api
import copy


class MeetingsCriteria(Criteria):
    """
    """

    def __init__(self, context):
        self.criteria = self.compute_criteria(context)

    def compute_criteria(self, context, must_choose_meeting=True):
        """ Gets global faceted criteria and unset hidealloption if needed
        """
        portal = api.portal.get()
        config_folder = getattr(portal, "config")
        faceted = getattr(config_folder, "faceted")
        self.context = faceted
        criteria = copy.deepcopy(self._criteria())
        if not must_choose_meeting:
            meetings_criteria = criteria[0]
            meetings_criteria.hidealloption = False
        return criteria


class ItemsCriteria(MeetingsCriteria):
    """
    """

    def __init__(self, context):
        self.criteria = self.compute_criteria(context, must_choose_meeting=False)
