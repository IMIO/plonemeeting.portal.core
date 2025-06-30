# -*- coding: utf-8 -*-
from plonemeeting.portal.core.tests.portal_test_case import PmPortalDemoFunctionalTestCase


class TestMeetingView(PmPortalDemoFunctionalTestCase):

    def test_call_meeting_view_as_manager(self):
        meeting = self.portal["belleville"].decisions.listFolderContents(
            {"portal_type": "Meeting"})[0]
        self.login_as_admin()
        request = self.portal.REQUEST
        view = meeting.restrictedTraverse("@@view")
        request.set('PUBLISHED', view)
        view()
        self.assertEqual(view.request.response.status, 200)

    def test_call_meeting_view_as_anonymous(self):
        meeting = self.portal["belleville"].decisions.listFolderContents(
            {"portal_type": "Meeting"})[-1]
        self.login_as_test()
        view = meeting.restrictedTraverse("@@view")
        view()
        self.assertEqual(view.request.response.status, 302)
        self.assertDictEqual(
            view.request.response.headers,
            {'location': 'http://nohost/plone/belleville/decisions#seance={}'.format(
                meeting.UID())})
