# -*- coding: utf-8 -*-
from plonemeeting.portal.core.migrations import PlonemeetingMigrator

import logging


logger = logging.getLogger("plonemeeting.portal.core")


class MigrateTo2500(PlonemeetingMigrator):

    def run(self):
        logger.info("Migrating to plonemeeting.portal.core 2500")
        self.ps.runImportStepFromProfile("profile-plonemeeting.portal.core:default", "rolemap")
        self.ps.runImportStepFromProfile("profile-plonemeeting.portal.core:default", "actions")
        logger.info("Migration to plonemeeting.portal.core 2500 done.")


def migrate(context):
    """
    DELIBE-287: gate the workflow/version 'history' toolbar action and the
    @@historyview page on the 'View History' permission instead of
    'Modify portal content', and grant 'View History' to Reader at the
    portal root so it flows down via acquisition to every institution
    content type. No workflow declares View History in its permission
    header, so acquisition is never cut.
    """
    migrator = MigrateTo2500(context)
    migrator.run()
    migrator.finish()
