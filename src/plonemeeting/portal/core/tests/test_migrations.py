# -*- coding: utf-8 -*-
from plonemeeting.portal.core.migrations.migrate_to_2406 import MigrateTo2406
from plonemeeting.portal.core.tests.portal_test_case import PmPortalDemoFunctionalTestCase


class TestMigrateTo2406(PmPortalDemoFunctionalTestCase):
    def test_backfills_meeting_type_from_institution(self):
        # demo meetings predate the field: no stored value
        self.assertIsNone(getattr(self.meeting, "meeting_type", None))
        migrator = MigrateTo2406(self.portal.portal_setup)
        migrator.run()
        self.assertEqual(self.meeting.meeting_type, self.institution.meeting_type)
