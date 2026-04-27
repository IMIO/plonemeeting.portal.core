# -*- coding: utf-8 -*-
from plonemeeting.portal.core.browser.meeting import MeetingAddForm
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

    def test_meeting_add_form_default_custom_info(self):
        self.login_as_admin()
        self.institution.default_meeting_extra_infos_text = "<p>my default</p>"
        add_form = MeetingAddForm(self.institution.decisions, self.portal.REQUEST)
        add_form.portal_type = "Meeting"
        add_form.updateFields()
        self.assertEqual(
            add_form.fields["custom_info"].field.default,
            "<p>my default</p>",
        )

    def test_meeting_edit_form_handle_apply_redirects_to_meeting(self):
        self.login_as_admin()
        request = self.portal.REQUEST
        edit_form = self.meeting.restrictedTraverse("@@edit")
        request.set("PUBLISHED", edit_form)
        edit_form()
        edit_form.handleApply(edit_form, None)
        utils_view = self.meeting.restrictedTraverse("@@utils_view")
        self.assertEqual(request.response.status, 302)
        self.assertEqual(
            request.response.headers["location"],
            utils_view.get_meeting_url(meeting=self.meeting),
        )

    def test_meeting_edit_form_handle_cancel_redirects_to_meeting(self):
        self.login_as_admin()
        request = self.portal.REQUEST
        edit_form = self.meeting.restrictedTraverse("@@edit")
        request.set("PUBLISHED", edit_form)
        edit_form()
        edit_form.handleCancel(edit_form, None)
        utils_view = self.meeting.restrictedTraverse("@@utils_view")
        self.assertEqual(request.response.status, 302)
        self.assertEqual(
            request.response.headers["location"],
            utils_view.get_meeting_url(meeting=self.meeting),
        )
