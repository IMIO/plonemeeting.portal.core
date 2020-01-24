# -*- coding: utf-8 -*-
import unittest

from plone.app.testing import TEST_USER_NAME
from plone.app.testing import login, logout

from plone import api
from plonemeeting.portal.core.testing import (
    PLONEMEETING_PORTAL_DEMO_FUNCTIONAL_TESTING,
    PLONEMEETING_PORTAL_CORE_INTEGRATION_TESTING,
)


class PmPortalTestCase(unittest.TestCase):
    layer = PLONEMEETING_PORTAL_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.portal.acl_users._doAddUser("manager", "secretmaster", ["Manager"], [])
        self.workflow = self.portal.portal_workflow

    def tearDown(self):
        logout()

    def login_as_manager(self):
        login(self.portal, "manager")

    def login_as_test(self):
        login(self.portal, TEST_USER_NAME)

    def create_object(self, portal_type, container=None):
        if not container:
            container = self.portal

        self.login_as_manager()
        portal_types = self.portal.portal_types
        parent_id = portal_types.constructContent(
            portal_type, container, "test_object", title="My {}".format(portal_type)
        )
        self.login_as_test()
        return self.portal[parent_id]


class PmPortalDemoFunctionalTestCase(PmPortalTestCase):

    layer = PLONEMEETING_PORTAL_DEMO_FUNCTIONAL_TESTING

    def setUp(self):
        super().setUp()
        self.institution = self.portal["amityville"]

        self.meeting = api.content.find(self.institution, portal_type="Meeting")[
            0
        ].getObject()
        self.item = api.content.find(self.meeting, portal_type="Item")[0].getObject()
        self.login_as_institution_manager()

    def login_as_institution_manager(self):
        login(self.portal, "amityville-manager")
