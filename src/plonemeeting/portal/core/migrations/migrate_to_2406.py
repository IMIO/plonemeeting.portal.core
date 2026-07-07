# -*- coding: utf-8 -*-
from plone import api
from plonemeeting.portal.core.migrations import PlonemeetingMigrator

import logging


logger = logging.getLogger("plonemeeting.portal.core")


class MigrateTo2406(PlonemeetingMigrator):
    def _store_meeting_type_on_meetings(self):
        brains = self.catalog(portal_type="Meeting")
        logger.info("Backfilling meeting_type on %d meetings", len(brains))
        for brain in brains:
            meeting = brain.getObject()
            institution = api.portal.get_navigation_root(meeting)
            meeting.meeting_type = getattr(institution, "meeting_type", None)

    def run(self):
        logger.info("Migrating to plonemeeting.portal.core 2406")
        self._store_meeting_type_on_meetings()
        logger.info("Migration to plonemeeting.portal.core 2406 done.")


def migrate(context):
    """Backfill the new Meeting.meeting_type field from each meeting's institution."""
    migrator = MigrateTo2406(context)
    migrator.run()
    migrator.finish()
