# -*- coding: utf-8 -*-

from eea.facetednavigation.criteria.handler import Criteria
from plone import api
from plonemeeting.portal.core.config import CONFIG_FOLDER_ID
from plonemeeting.portal.core.config import FACETED_DEC_FOLDER_ID
from plonemeeting.portal.core.config import FACETED_DEC_MANAGER_CRITERIA
from plonemeeting.portal.core.config import FACETED_PUB_FOLDER_ID
from plonemeeting.portal.core.config import FACETED_PUB_MANAGER_CRITERIA

import copy


class MeetingsCriteria(Criteria):
    """
    """

    def __init__(self, context):
        self.criteria = self.compute_criteria(context)

    def compute_criteria(self, context):
        """ Use faceted criteria defined globally
        """
        portal = api.portal.get()
        config_folder = getattr(portal, CONFIG_FOLDER_ID)
        faceted = getattr(config_folder, FACETED_DEC_FOLDER_ID)
        self.context = faceted
        criteria = copy.deepcopy(self._criteria())
        # remove FACETED_DEC_MANAGER_CRITERIA if current user is anonymous
        if api.user.is_anonymous():
            criteria = [criterion for criterion in criteria
                        if criterion.__name__ not in FACETED_DEC_MANAGER_CRITERIA]
        return criteria


class PublicationsCriteria(Criteria):
    """
    """

    def __init__(self, context):
        self.criteria = self.compute_criteria(context)

    def compute_criteria(self, context):
        """ Use faceted criteria defined globally
        """
        portal = api.portal.get()
        config_folder = getattr(portal, CONFIG_FOLDER_ID)
        faceted = getattr(config_folder, FACETED_PUB_FOLDER_ID)
        self.context = faceted
        criteria = copy.deepcopy(self._criteria())
        # remove FACETED_PUB_MANAGER_CRITERIA if current user is anonymous
        if api.user.is_anonymous():
            criteria = [criterion for criterion in criteria
                        if criterion.__name__ not in FACETED_PUB_MANAGER_CRITERIA]
        return criteria
