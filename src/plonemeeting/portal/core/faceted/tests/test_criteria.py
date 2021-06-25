# -*- coding: utf-8 -*-

from plonemeeting.portal.core.config import APP_FOLDER_ID
from plonemeeting.portal.core.config import CONFIG_FOLDER_ID
from plonemeeting.portal.core.config import FACETED_FOLDER_ID
from plonemeeting.portal.core.testing import PLONEMEETING_PORTAL_DEMO_FUNCTIONAL_TESTING
from eea.facetednavigation.interfaces import ICriteria

import unittest


class TestFacetedCriteria(unittest.TestCase):
    layer = PLONEMEETING_PORTAL_DEMO_FUNCTIONAL_TESTING

    @property
    def amityville(self):
        return self.layer["portal"]["amityville"]

    @property
    def belleville(self):
        return self.layer["portal"]["belleville"]

    def test_compute_criteria(self):
        """Global defined criteria are used for every institutions."""
        global_criteria = ICriteria(self.layer["portal"][CONFIG_FOLDER_ID][FACETED_FOLDER_ID])
        for faceted_folder in (self.amityville[APP_FOLDER_ID], self.belleville[APP_FOLDER_ID]):
            criteria = ICriteria(faceted_folder)
            self.assertEqual(
                global_criteria._criteria(),
                criteria._criteria(),
            )
