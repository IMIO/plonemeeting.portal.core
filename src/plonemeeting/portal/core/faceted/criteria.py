# -*- coding: utf-8 -*-

from eea.facetednavigation.criteria.handler import Criteria
from plone import api
import copy

from plonemeeting.portal.core.config import CONFIG_FOLDER_ID
from plonemeeting.portal.core.config import FACETED_FOLDER_ID


class MeetingsCriteria(Criteria):
    """
    """

    def __init__(self, context):
        self.criteria = self.compute_criteria(context)

    def compute_criteria(self, context, must_choose_meeting=True):
        """ Gets global faceted criteria and unset hidealloption if needed
        """
        portal = api.portal.get()
        config_folder = getattr(portal, CONFIG_FOLDER_ID)
        faceted = getattr(config_folder, FACETED_FOLDER_ID)
        self.context = faceted
        criteria = copy.deepcopy(self._criteria())
        if must_choose_meeting:
            return criteria
        for criterion in criteria:
            if criterion.getId() == "seance":
                criterion.hidealloption = False
        return criteria


class ItemsCriteria(MeetingsCriteria):
    """
    """

    def __init__(self, context):
        self.criteria = self.compute_criteria(context, must_choose_meeting=False)
