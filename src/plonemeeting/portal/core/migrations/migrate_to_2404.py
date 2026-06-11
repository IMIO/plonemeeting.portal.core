# -*- coding: utf-8 -*-
from plone.base.interfaces.syndication import IFeedSettings
from plonemeeting.portal.core.config import DEC_FOLDER_ID
from plonemeeting.portal.core.config import PUB_FOLDER_ID
from plonemeeting.portal.core.migrations import PlonemeetingMigrator

import logging


logger = logging.getLogger("plonemeeting.portal.core")


class MigrateTo2404(PlonemeetingMigrator):
    def _enable_institution_feeds(self):
        brains = self.catalog(portal_type="Institution")
        logger.info(
            "Enabling syndication on the decisions/publications folders of %d institutions", len(brains)
        )
        for brain in brains:
            institution = brain.getObject()
            for folder_id in (DEC_FOLDER_ID, PUB_FOLDER_ID):
                folder = institution.get(folder_id)
                if folder is None:
                    logger.warning("No '%s' folder in %s, skipping", folder_id, brain.getPath())
                    continue
                IFeedSettings(folder).enabled = True

    def run(self):
        logger.info("Migrating to plonemeeting.portal.core 2404")
        self.ps.runImportStepFromProfile("profile-plonemeeting.portal.core:default", "plone.app.registry")
        self.ps.runImportStepFromProfile("profile-plonemeeting.portal.core:default", "actions")
        self._enable_institution_feeds()
        logger.info("Migration to plonemeeting.portal.core 2404 done.")


def migrate(context):
    """
    This migration function will:
       1) Re-import the registry profile step to make sure syndication is allowed site-wide.
       2) Re-import the actions profile step to make the "RSS feed" document action visible.
       3) Enable RSS/Atom feeds on the decisions and publications folders of every institution.
    """
    migrator = MigrateTo2404(context)
    migrator.run()
    migrator.finish()
