# -*- coding: utf-8 -*-

from plonemeeting.portal.core.testing import PLONEMEETING_PORTAL_DEMO_FUNCTIONAL_TESTING
from eea.facetednavigation.interfaces import ICriteria

import unittest


class TestFacetedCriteria(unittest.TestCase):
    layer = PLONEMEETING_PORTAL_DEMO_FUNCTIONAL_TESTING

    @property
    def belleville(self):
        return self.layer["portal"]["belleville"]

    def test_compute_criteria(self):
        criteria = ICriteria(self.belleville["meetings"])
        # The criteria must be the same
        self.assertListEqual(
            sorted([c.__dict__ for c in criteria._criteria()]),
            sorted([c.__dict__ for c in criteria.criteria]),
        )

    def test_items_criteria(self):
        criteria = ICriteria(self.belleville["items-1"])
        self.assertListEqual(
            sorted([c.__dict__ for c in criteria._criteria() if c.getId() != "seance"]),
            sorted([c.__dict__ for c in criteria.criteria if c.getId() != "seance"]),
        )
        old_criterion = [c for c in criteria._criteria() if c.getId() == "seance"][0]
        new_criterion = [c for c in criteria.criteria if c.getId() == "seance"][0]
        self.assertTrue(getattr(old_criterion, "hidealloption", True))
        self.assertFalse(new_criterion.hidealloption)
