# -*- coding: utf-8 -*-


from eea.facetednavigation.interfaces import ICriteria
from plone import api
from plonemeeting.portal.core.config import APP_FOLDER_ID
from plonemeeting.portal.core.config import CONFIG_FOLDER_ID
from plonemeeting.portal.core.config import FACETED_FOLDER_ID
from plonemeeting.portal.core.faceted.widgets.select import SelectMeetingWidget
from plonemeeting.portal.core.faceted.widgets.sort import ItemsSortWidget
from plonemeeting.portal.core.testing import PLONEMEETING_PORTAL_DEMO_FUNCTIONAL_TESTING
from plonemeeting.portal.core.tests.portal_test_case import PmPortalTestCase
from plonemeeting.portal.core.utils import format_meeting_date_and_state


class TestFacetedCriteria(PmPortalTestCase):
    layer = PLONEMEETING_PORTAL_DEMO_FUNCTIONAL_TESTING

    @property
    def amityville(self):
        return self.layer["portal"]["amityville"]

    @property
    def belleville(self):
        return self.layer["portal"]["belleville"]

    def test_compute_criteria(self):
        """Global defined criteria are used for every institutions."""
        global_criteria = ICriteria(self.layer["portal"][CONFIG_FOLDER_ID][FACETED_FOLDER_ID])
        for faceted_folder in (self.amityville[APP_FOLDER_ID], self.belleville[APP_FOLDER_ID]):
            criteria = ICriteria(faceted_folder)
            self.assertEqual(
                global_criteria._criteria(),
                criteria._criteria(),
            )

    def test_select_widget(self):
        # setup, reuse "seance" and "matiere" criteria
        request = self.layer["request"]
        faceted_folder = self.belleville[APP_FOLDER_ID]
        criteria = ICriteria(faceted_folder)
        seance_data = criteria.get("seance")
        self.assertIsNone(seance_data.default)
        seance_widget = SelectMeetingWidget(faceted_folder, request, data=seance_data)
        matiere_data = criteria.get("matiere")
        self.assertIsNone(matiere_data.default)
        matiere_widget = SelectMeetingWidget(faceted_folder, request, data=matiere_data)
        # a widget other than "seance" will return ""
        self.assertEqual(matiere_widget.default, "")
        # but the "seance" widget returns the last meeting
        # we have the most recent meeting, so the meeting of "13 March 2020 (18:00) — decision"
        catalog = self.portal.portal_catalog
        meeting_uid = seance_widget.default
        brain = catalog(UID=meeting_uid)[0]
        title = format_meeting_date_and_state(brain.date_time, brain.review_state)
        self.assertEqual(title, "13 March 2020 (18:00) — decision")
        # when no meetings exist, default is ""
        for meeting_uid, meeting_title in seance_widget.vocabulary():
            api.content.delete(catalog(UID=meeting_uid)[0].getObject())
        self.assertEqual(seance_widget.vocabulary(), [])
        self.assertEqual(matiere_widget.default, "")
        self.assertEqual(seance_widget.default, "")

    def test_sort_widget(self):
        # setup, reuse "sort" criterion
        request = self.layer["request"]
        faceted_folder = self.belleville[APP_FOLDER_ID]
        criteria = ICriteria(faceted_folder)
        sort_data = criteria.get("tri")
        self.assertIsNone(sort_data.default)
        sort_widget = ItemsSortWidget(faceted_folder, request, data=sort_data)
        # when no meeting selected in "seance"
        self.assertFalse("seance" in request.form)
        self.assertEqual(sort_widget.query(request.form),
                         {'sort_on': ['linkedMeetingDate', 'sortable_number'],
                          'sort_order': ['descending', 'ascending']})
        meetings = self.belleville.getFolderContents({"portal_type": "Meeting"})
        request.form["seance"] = meetings[0].UID
        self.assertEqual(sort_widget.query(request.form),
                         {'sort_on': ['sortable_number'],
                          'sort_order': ['ascending']})
