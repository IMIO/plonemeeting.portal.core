# -*- coding: utf-8 -*-
from mockito import unstub
from plone import api
from plone.app.testing import login
from plone.app.testing import logout
from plone.app.testing import TEST_USER_NAME
from plonemeeting.portal.core.testing import PLONEMEETING_PORTAL_CORE_INTEGRATION_TESTING
from plonemeeting.portal.core.testing import PLONEMEETING_PORTAL_DEMO_FUNCTIONAL_TESTING
from plonemeeting.portal.core.tests import PM_ADMIN_USER
from plonemeeting.portal.core.tests import PM_USER_PASSWORD
from plonemeeting.portal.core.utils import get_decisions_managers_group_id

import unittest


IMG_BASE64_DATA = (
    "data:image/gif;base64,R0lGODlhCgAKAPcAAP////79/f36+/3z8/zy8/rq7Prm6Pnq7P"
    "je4vTx8vPg5O6gqe2gqOq4v+igqt9tetxSYNs7Tdo5TNc5TNUbMdUbMNQRKNIKIdIJINIGHdEGHtEDGtACFdAA"
    "FtAAFNAAEs8AFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAACIAIP3sAAoACBL2OAAAAPjHWRQAABUKiAAAABL2FAAAAhL+dPkBhPm4MP"
    "///xL2YPZNegAAAAAQAAAABgAAAAAAABL2wAAAAAAARRL25PEPfxQAAPEQAAAAAAAAA/3r+AAAAAAAGAAAABL2"
    "uAAAQgAAABL2pAAAAAAAAAAAAAAADAAAAgABAfDTAAAAmAAAAAAAAAAAABL27Mku0AAQAAAAAAAAAEc1MUaDsA"
    "AAGBL3FPELyQAAAAABEgAAAwAAAQAAAxL22AAAmBL+dPO4dPPKQP///0c70EUoOQAAmMku0AAQABL3TAAAAEaD"
    "sEc1MUaDsAAABkT98AABEhL3wAAALAAAQAAAQBL3kQAACSH5BAEAAAAALAAAAAAKAAoAQAhGAAEIHEhw4IIIFC"
    "AsKCBwQAQQFyKCeKDAIEKFDAE4hBiRA0WCAwwUBLCAA4cMICg0YIjAQoaIFzJMSCCw5EkOKjM2FDkwIAA7"
)


class PmPortalTestCase(unittest.TestCase):
    layer = PLONEMEETING_PORTAL_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.portal_url = self.portal.absolute_url()
        self.portal.acl_users._doAddUser(PM_ADMIN_USER, PM_USER_PASSWORD, ["Manager"], [])
        self.login_as_admin()
        self.catalog = self.portal.portal_catalog
        self.workflow = self.portal.portal_workflow
        # show entire diff when a test fails
        self.maxDiff = None

    def tearDown(self):
        # avoid cascading failure because unstub wasn't called
        unstub()
        logout()

    def login_as_admin(self):
        login(self.portal, PM_ADMIN_USER)

    def login_as_test(self):
        login(self.portal, TEST_USER_NAME)

    def logout(self):
        logout()

    def create_object(self, portal_type, container=None):
        if not container:
            container = self.portal

        self.login_as_admin()
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
        self.portal.acl_users._doAddUser("amityville-decisions-manager2", PM_USER_PASSWORD, [], [])
        group = api.group.get(get_decisions_managers_group_id(self.institution))
        group.addMember("amityville-decisions-manager2")
        self.meeting = api.content.find(self.institution, portal_type="Meeting")[0].getObject()
        self.item = api.content.find(self.meeting, portal_type="Item")[0].getObject()
        self.login_as_decisions_manager()

    def login_as_decisions_manager(self):
        login(self.portal, "amityville-decisions-manager")

    def login_as_decisions_manager2(self):
        login(self.portal, "amityville-decisions-manager2")

    def login_as_publications_manager(self):
        login(self.portal, "amityville-publications-manager")

    def login_as_institution_manager(self):
        login(self.portal, "belleville-decisions-manager")
