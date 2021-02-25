# -*- coding: utf-8 -*-
from plone import api
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.testing import z2
from plone.testing.zope import makeTestRequest

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

        # Patch collective.fingerpointing
        from collective.fingerpointing import utils

        def patched_getRequest():
            return makeTestRequest(environ={})

        utils.getRequest = patched_getRequest

    def setUpPloneSite(self, portal):
        with api.env.adopt_roles(['Manager']):
            applyProfile(portal, "plonemeeting.portal.core:default")
        import transaction

        transaction.commit()

    def tearDownZope(self, app):
        import transaction

        transaction.abort()


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


class PlonemeetingPortalDemoLayer(PlonemeetingPortalCoreLayer):
    def setUpPloneSite(self, portal):
        with api.env.adopt_roles(['Manager']):
            super(PlonemeetingPortalDemoLayer, self).setUpPloneSite(portal)
            applyProfile(portal, "plonemeeting.portal.core:demo")
        import transaction

        transaction.commit()


PLONEMEETING_PORTAL_DEMO_FIXTURE = PlonemeetingPortalDemoLayer()


PLONEMEETING_PORTAL_DEMO_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(PLONEMEETING_PORTAL_DEMO_FIXTURE,),
    name="PlonemeetingPortalDemoLayer:FunctionalTesting",
)
