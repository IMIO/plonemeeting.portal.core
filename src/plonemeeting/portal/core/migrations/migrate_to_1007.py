# -*- coding: utf-8 -*-

from imio.migrator.migrator import Migrator
from plone.api.portal import set_registry_record
from plonemeeting.portal.core.config import DELIB_ANONYMIZED_TEXT
from plonemeeting.portal.core.config import RGPD_MASKED_TEXT

import logging


logger = logging.getLogger("plonemeeting.portal.core")


class MigrateTo1007(Migrator):

    def run(self):
        logger.info("Migrating to plonemeeting.portal.core 1007...")
        self._init_gdpr_records()

    def _init_gdpr_records(self):
        logger.info("Initilizing new registry records values...")
        set_registry_record("plonemeeting.portal.core.rgpd_masked_text_redirect_path", "#rgpd")
        set_registry_record("plonemeeting.portal.core.rgpd_masked_text_placeholder", RGPD_MASKED_TEXT)
        set_registry_record("plonemeeting.portal.core.delib_masked_gdpr", DELIB_ANONYMIZED_TEXT)
        logger.info("Done.")


def migrate(context):
    """
    This migration function will:
       1) initialize gdpr registry records
    """
    migrator = MigrateTo1007(context)
    migrator.run()
    migrator.finish()
