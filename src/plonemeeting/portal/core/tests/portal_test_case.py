# -*- coding: utf-8 -*-
from mockito import unstub
from plone import api
from plone.app.testing import login
from plone.app.testing import logout
from plone.app.testing import TEST_USER_NAME
from plonemeeting.portal.core.testing import PLONEMEETING_PORTAL_CORE_INTEGRATION_TESTING
from plonemeeting.portal.core.testing import PLONEMEETING_PORTAL_DEMO_FUNCTIONAL_TESTING

import unittest


IMG_BASE64_DATA = "data:image/gif;base64,R0lGODlhCgAKAPcAAP////79/f36+/3z8/zy8/rq7Prm6Pnq7P" \
    "je4vTx8vPg5O6gqe2gqOq4v+igqt9tetxSYNs7Tdo5TNc5TNUbMdUbMNQRKNIKIdIJINIGHdEGHtEDGtACFdAA" \
    "FtAAFNAAEs8AFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" \
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" \
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" \
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" \
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" \
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" \
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAACIAIP3sAAoACBL2OAAAAPjHWRQAABUKiAAAABL2FAAAAhL+dPkBhPm4MP" \
    "///xL2YPZNegAAAAAQAAAABgAAAAAAABL2wAAAAAAARRL25PEPfxQAAPEQAAAAAAAAA/3r+AAAAAAAGAAAABL2" \
    "uAAAQgAAABL2pAAAAAAAAAAAAAAADAAAAgABAfDTAAAAmAAAAAAAAAAAABL27Mku0AAQAAAAAAAAAEc1MUaDsA" \
    "AAGBL3FPELyQAAAAABEgAAAwAAAQAAAxL22AAAmBL+dPO4dPPKQP///0c70EUoOQAAmMku0AAQABL3TAAAAEaD" \
    "sEc1MUaDsAAABkT98AABEhL3wAAALAAAQAAAQBL3kQAACSH5BAEAAAAALAAAAAAKAAoAQAhGAAEIHEhw4IIIFC" \
    "AsKCBwQAQQFyKCeKDAIEKFDAE4hBiRA0WCAwwUBLCAA4cMICg0YIjAQoaIFzJMSCCw5EkOKjM2FDkwIAA7"


class PmPortalTestCase(unittest.TestCase):
    layer = PLONEMEETING_PORTAL_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.portal_url = self.portal.absolute_url()
        self.portal.acl_users._doAddUser("manager", "secretmaster", ["Manager"], [])
        self.login_as_manager()
        self.workflow = self.portal.portal_workflow
        # show entire diff when a test fails
        self.maxDiff = None

    def tearDown(self):
        # avoid cascading failure because unstub wasn't called
        unstub()
        logout()

    def login_as_manager(self):
        login(self.portal, "manager")

    def login_as_test(self):
        login(self.portal, TEST_USER_NAME)

    def logout(self):
        logout()

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
        self.amittyville = self.portal["amityville"]
        self.amittyville.plonemeeting_url = "http://localhost:20081/demo"
        self.amittyville.password = "Meeting_12"

        self.belleville = self.portal["belleville"]
        self.belleville.plonemeeting_url = "http://localhost:20081/demo"
        self.belleville.password = "Meeting_12"

        self.meeting = api.content.find(self.amittyville, portal_type="Meeting")[
            0
        ].getObject()
        self.item = api.content.find(self.meeting, portal_type="Item")[0].getObject()
        self.login_as_institution_manager()

    def login_as_institution_manager(self):
        login(self.portal, "amityville-manager")
