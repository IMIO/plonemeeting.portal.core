# -*- coding: utf-8 -*-

from collective.fingerpointing import utils as fp_utils
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.testing.zope import INTEGRATION_TESTING
from plone.testing.zope import makeTestRequest
from plone.testing.zope import WSGI_SERVER

import collective.documentgenerator
import plonemeeting.portal.core
import transaction


__old__getRequest = fp_utils.getRequest


class PlonemeetingPortalCoreLayer(PloneSandboxLayer):

    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        import plone.restapi

        self.loadZCML(package=plone.restapi)
        self.loadZCML(package=collective.documentgenerator)
        self.loadZCML(package=plonemeeting.portal.core)

        # Patch collective.fingerpointing

        def patched_getRequest():
            return makeTestRequest(environ={})

        fp_utils.getRequest = patched_getRequest

    def setUpPloneSite(self, portal):
        applyProfile(portal, "collective.documentgenerator:default")
        applyProfile(portal, "plonemeeting.portal.core:default")
        transaction.commit()


PLONEMEETING_PORTAL_CORE_FIXTURE = PlonemeetingPortalCoreLayer()


PLONEMEETING_PORTAL_CORE_INTEGRATION_TESTING = IntegrationTesting(
    bases=(PLONEMEETING_PORTAL_CORE_FIXTURE,
           INTEGRATION_TESTING),
    name="PlonemeetingPortalCoreLayer:IntegrationTesting",
)


PLONEMEETING_PORTAL_CORE_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(PLONEMEETING_PORTAL_CORE_FIXTURE,
           WSGI_SERVER),
    name="PlonemeetingPortalCoreLayer:FunctionalTesting",
)


PLONEMEETING_PORTAL_CORE_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        PLONEMEETING_PORTAL_CORE_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        WSGI_SERVER,
    ),
    name="PlonemeetingPortalCoreLayer:AcceptanceTesting",
)


class PlonemeetingPortalDemoLayer(PlonemeetingPortalCoreLayer):
    def setUpPloneSite(self, portal):
        applyProfile(portal, "plonemeeting.portal.core:demo")
        transaction.commit()


PLONEMEETING_PORTAL_DEMO_FIXTURE = PlonemeetingPortalDemoLayer()


PLONEMEETING_PORTAL_DEMO_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(PLONEMEETING_PORTAL_DEMO_FIXTURE,),
    name="PlonemeetingPortalDemoLayer:FunctionalTesting",
)
