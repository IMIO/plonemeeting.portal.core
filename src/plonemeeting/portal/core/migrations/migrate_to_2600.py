# -*- coding: utf-8 -*-
from plone.registry.interfaces import IRegistry
from plonemeeting.portal.core.migrations import PlonemeetingMigrator
from zope.component import getUtility

import logging


logger = logging.getLogger("plonemeeting.portal.core")

PRIMARY_COLOR_RECORD = "imio.emailkit.theme.primary_color"
# The magenta of the portal, and the default colour of the kit. A record that
# holds the kit default tells this step that nobody set a colour by hand.
PORTAL_PRIMARY_COLOR = "#DE007B"
KIT_PRIMARY_COLOR = "#e6007e"


class MigrateTo2600(PlonemeetingMigrator):
    def _install_emailkit(self):
        """Install imio.emailkit.

        The metadata.xml dependency on imio.emailkit:default applies only when
        a site installs or reinstalls this profile. Thus upgraded sites must
        install the add-on here. Otherwise they do not get the restyled Plone
        mails, and they do not get the theme records that the next step sets.
        """
        if not self.qi.is_product_installed("imio.emailkit"):
            self.qi.install_product("imio.emailkit")
            logger.info("Installed imio.emailkit")

    def _set_email_primary_color(self):
        """Set the primary_color of the kit to the magenta of the portal.

        This step writes one record only. A new import of the full registry
        step resets all values that a site changed after the install, for
        example the Plausible API key and the tile server of the homepage map.
        The step keeps a colour that a user set in Site Setup. Thus it is safe
        to run the step again.
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
    """Install imio.emailkit. Set the primary colour of the email theme to the
    magenta of the portal."""
    migrator = MigrateTo2600(context)
    migrator.run()
    migrator.finish()
