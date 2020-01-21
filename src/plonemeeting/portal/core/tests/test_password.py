# -*- coding: utf-8 -*-
import unittest

from plonemeeting.portal.core.passwords import PloneMeetingPasswordValidator
from plonemeeting.portal.core.testing import PLONEMEETING_PORTAL_DEMO_FUNCTIONAL_TESTING


class TestPloneMeetingPasswordValidator(unittest.TestCase):

    layer = PLONEMEETING_PORTAL_DEMO_FUNCTIONAL_TESTING

    def test_validate(self):
        invalid_label = "Passwords must be at least 8 characters in length."
        self.assertEqual(
            invalid_label, PloneMeetingPasswordValidator.validate("", None)
        )

        self.assertEqual(
            invalid_label, PloneMeetingPasswordValidator.validate("1234567", None)
        )

        self.assertIsNone(PloneMeetingPasswordValidator.validate("12345678", None))
        self.assertIsNone(PloneMeetingPasswordValidator.validate("        ", None))
        self.assertIsNone(PloneMeetingPasswordValidator.validate("azertyui", None))
        self.assertIsNone(
            PloneMeetingPasswordValidator.validate("azertyuiopqsdfghjklmwxcvbn", None)
        )
        self.assertIsNone(PloneMeetingPasswordValidator.validate("7V4#VAku", None))
        self.assertIsNone(
            PloneMeetingPasswordValidator.validate(
                "cZ2mtREhxp6CTPEoyz6Aqs$5BvubreUjpo7fKHB*Ng6KVaMFB4P77Gi!5Q5oEiCSDh^"
                "xKDSe#aRSb%iT@7upnq4C&gZoVffZj^#M9kZS$bhBsyqsvhDKnNbZy#M$p3Hb",
                None,
            )
        )
