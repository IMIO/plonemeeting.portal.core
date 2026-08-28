# -*- coding: utf-8 -*-
from plone.registry import field
from plone.registry import Record
from plone.registry.interfaces import IRegistry
from plonemeeting.portal.core.migrations import PlonemeetingMigrator
from zope.component import getUtility

import logging


logger = logging.getLogger("plonemeeting.portal.core")

DEFAULT_TILES_URL = "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
DEFAULT_ATTRIBUTION = (
    'Carte &copy; <a href="http://osm.org/copyright">OpenStreetMap</a>'
    ' | Données &copy; <a href="https://www.ngi.be/website/fr/">NGI-IGN</a>'
)


class MigrateTo2501(PlonemeetingMigrator):
    def _add_map_registry_records(self):
        """Add the homepage map records one-by-one instead of re-importing the
        whole registry step, which would reset customized values (e.g. the
        Plausible API key) to their profile defaults."""
        registry = getUtility(IRegistry)
        records = (
            ("plonemeeting.portal.core.map_tiles_url", "Map tile server URL", DEFAULT_TILES_URL),
            ("plonemeeting.portal.core.map_attribution", "Map attribution", DEFAULT_ATTRIBUTION),
        )
        for name, title, value in records:
            if name in registry.records:
                logger.info("Registry record %s already exists, skipping", name)
                continue
            registry.records[name] = Record(field.TextLine(title=title, required=False), value)
            logger.info("Added registry record %s", name)

    def run(self):
        logger.info("Migrating to plonemeeting.portal.core 2501")
        self._add_map_registry_records()
        logger.info("Migration to plonemeeting.portal.core 2501 done.")


def migrate(context):
    """Add the homepage map tile server URL and attribution registry records."""
    migrator = MigrateTo2501(context)
    migrator.run()
    migrator.finish()
