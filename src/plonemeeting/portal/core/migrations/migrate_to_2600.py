# -*- coding: utf-8 -*-
from plone.registry.interfaces import IRegistry
from plonemeeting.portal.core.migrations import PlonemeetingMigrator
from zope.component import getUtility

import logging


logger = logging.getLogger("plonemeeting.portal.core")

PRIMARY_COLOR_RECORD = "imio.emailkit.theme.primary_color"
# The portal's magenta, and the colour the kit ships as its own default. An
# untouched record holds the latter, which is how this step knows nobody has
# picked a colour by hand yet.
PORTAL_PRIMARY_COLOR = "#DE007B"
KIT_PRIMARY_COLOR = "#e6007e"


class MigrateTo2600(PlonemeetingMigrator):
    def _install_emailkit(self):
        """Install imio.emailkit.

        The metadata.xml dependency on imio.emailkit:default only applies on a
        fresh (re)install of our profile, so upgraded sites have to install the
        add-on here or they get neither the restyled Plone mails nor the theme
        records the next step writes to.
        """
        if not self.qi.is_product_installed("imio.emailkit"):
            self.qi.install_product("imio.emailkit")
            logger.info("Installed imio.emailkit")

    def _set_email_primary_color(self):
        """Point the kit's primary_color at the portal's magenta.

        One record, written by hand: re-importing our whole registry step would
        reset every value a site has customized since (the Plausible API key,
        the homepage map tile server). A colour somebody already picked in Site
        Setup is left alone, which also makes the step re-runnable.
        """
        registry = getUtility(IRegistry)
        if PRIMARY_COLOR_RECORD not in registry.records:
            logger.warning(
                "No %s record; is imio.emailkit installed?", PRIMARY_COLOR_RECORD
            )
            return
        current = registry[PRIMARY_COLOR_RECORD]
        if current not in (None, "", KIT_PRIMARY_COLOR, PORTAL_PRIMARY_COLOR):
            logger.info(
                "%s is customized (%s), leaving it alone", PRIMARY_COLOR_RECORD, current
            )
            return
        registry[PRIMARY_COLOR_RECORD] = PORTAL_PRIMARY_COLOR
        logger.info("Set %s to %s", PRIMARY_COLOR_RECORD, PORTAL_PRIMARY_COLOR)

    def run(self):
        logger.info("Migrating to plonemeeting.portal.core 2600")
        self._install_emailkit()
        self._set_email_primary_color()
        logger.info("Migration to plonemeeting.portal.core 2600 done.")


def migrate(context):
    """Install imio.emailkit and set the email theme's primary colour to the
    portal's magenta."""
    migrator = MigrateTo2600(context)
    migrator.run()
    migrator.finish()
