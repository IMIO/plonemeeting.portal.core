# -*- coding: utf-8 -*-
from plonemeeting.portal.core.migrations import PlonemeetingMigrator

import logging


logger = logging.getLogger("plonemeeting.portal.core")


class MigrateTo2500(PlonemeetingMigrator):
    def run(self):
        logger.info("Migrating to plonemeeting.portal.core 2500")
        self.ps.runImportStepFromProfile(
            "profile-plonemeeting.portal.core:default", "typeinfo"
        )
        logger.info("Migration to plonemeeting.portal.core 2500 done.")


def migrate(context):
    """
    Re-import typeinfo to register the new authentication fieldset
    (authentication + sso_realm_id) on Institution (DELIBE-297).
    """
    migrator = MigrateTo2500(context)
    migrator.run()
    migrator.finish()
