# -*- coding: utf-8 -*-
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.testing import z2

import plonemeeting.portal.core


class PlonemeetingPortalCoreLayer(PloneSandboxLayer):

    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        import plone.restapi

        self.loadZCML(package=plone.restapi)
        self.loadZCML(package=plonemeeting.portal.core)

    def setUpPloneSite(self, portal):
        applyProfile(portal, "plonemeeting.portal.core:default")


PLONEMEETING_PORTAL_CORE_FIXTURE = PlonemeetingPortalCoreLayer()


PLONEMEETING_PORTAL_CORE_INTEGRATION_TESTING = IntegrationTesting(
    bases=(PLONEMEETING_PORTAL_CORE_FIXTURE,),
    name="PlonemeetingPortalCoreLayer:IntegrationTesting",
)


PLONEMEETING_PORTAL_CORE_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(PLONEMEETING_PORTAL_CORE_FIXTURE,),
    name="PlonemeetingPortalCoreLayer:FunctionalTesting",
)


PLONEMEETING_PORTAL_CORE_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        PLONEMEETING_PORTAL_CORE_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        z2.ZSERVER_FIXTURE,
    ),
    name="PlonemeetingPortalCoreLayer:AcceptanceTesting",
)
