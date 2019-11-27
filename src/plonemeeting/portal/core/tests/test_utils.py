# -*- coding: utf-8 -*-

import unittest
from datetime import datetime
from plonemeeting.portal.core.utils import format_meeting_date
from plonemeeting.portal.core.testing import PLONEMEETING_PORTAL_CORE_INTEGRATION_TESTING


class TestUtils(unittest.TestCase):
    layer = PLONEMEETING_PORTAL_CORE_INTEGRATION_TESTING

    def test_format_meeting_date(self):
        date = datetime(2019, 12, 31, 23, 59)
        # Base test
        formated_meeting_date = format_meeting_date(date)
        self.assertEqual(formated_meeting_date, u"31 December 2019 (23:59)")
        # Test translation
        french_formated_meeting_date = format_meeting_date(date, lang='fr')
        self.assertEqual(french_formated_meeting_date, u"31 Décembre 2019 (23:59)")
        # Test custom format
        french_custom_formated_meeting_date = format_meeting_date(date, format='%A %d %B %Y', lang='fr')
        self.assertEqual(french_custom_formated_meeting_date, u"Mardi 31 Décembre 2019")



