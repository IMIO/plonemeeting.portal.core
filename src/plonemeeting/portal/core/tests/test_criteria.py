# -*- coding: utf-8 -*-

from eea.facetednavigation.interfaces import ICriteria
from imio.helpers.content import uuidToCatalogBrain
from imio.helpers.content import uuidToObject
from plone import api
from plonemeeting.portal.core.config import CONFIG_FOLDER_ID
from plonemeeting.portal.core.config import DEC_FOLDER_ID
from plonemeeting.portal.core.config import FACETED_DEC_FOLDER_ID
from plonemeeting.portal.core.config import FACETED_PUB_FOLDER_ID
from plonemeeting.portal.core.config import PUB_FOLDER_ID
from plonemeeting.portal.core.faceted.widgets.select import SelectMeetingWidget
from plonemeeting.portal.core.faceted.widgets.sort import ItemsSortWidget
from plonemeeting.portal.core.testing import PLONEMEETING_PORTAL_DEMO_FUNCTIONAL_TESTING
from plonemeeting.portal.core.tests.portal_test_case import PmPortalTestCase
from plonemeeting.portal.core.utils import format_meeting_date_and_state


class TestFacetedCriteria(PmPortalTestCase):
    layer = PLONEMEETING_PORTAL_DEMO_FUNCTIONAL_TESTING

    @property
    def amityville(self):
        return self.portal["amityville"]

    @property
    def belleville(self):
        return self.portal["belleville"]

    def test_compute_criteria(self):
        """Global defined criteria are used for every institutions."""
        global_dec_criteria = ICriteria(self.layer["portal"][CONFIG_FOLDER_ID][FACETED_DEC_FOLDER_ID])
        for faceted_folder in (self.amityville[DEC_FOLDER_ID], self.belleville[DEC_FOLDER_ID]):
            criteria = ICriteria(faceted_folder)
            self.assertEqual(
                global_dec_criteria._criteria(),
                criteria._criteria(),
            )
        global_pub_criteria = ICriteria(self.layer["portal"][CONFIG_FOLDER_ID][FACETED_PUB_FOLDER_ID])
        for faceted_folder in (self.amityville[PUB_FOLDER_ID], self.belleville[PUB_FOLDER_ID]):
            criteria = ICriteria(faceted_folder)
            self.assertEqual(
                global_pub_criteria._criteria(),
                criteria._criteria(),
            )


    def test_select_widget(self):
        # setup, reuse "seance" and "matiere" criteria
        request = self.layer["request"]
        faceted_folder = self.belleville[DEC_FOLDER_ID]
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
        meeting_uid = seance_widget.default
        brain = uuidToCatalogBrain(meeting_uid)
        title = format_meeting_date_and_state(brain.date_time, brain.review_state)
        self.assertEqual(title, "13 March 2020 (18:00) — decision")
        # when no meetings exist, default is ""
        for meeting_uid, meeting_title in seance_widget.vocabulary():
            api.content.delete(uuidToObject(meeting_uid))
        self.assertEqual(seance_widget.vocabulary(), [])
        self.assertEqual(matiere_widget.default, "")
        self.assertEqual(seance_widget.default, "")

    def test_sort_widget(self):
        # setup, reuse "sort" criterion
        request = self.layer["request"]
        decisions_folder = self.belleville[DEC_FOLDER_ID]
        criteria = ICriteria(decisions_folder)
        sort_data = criteria.get("tri")
        self.assertIsNone(sort_data.default)
        sort_widget = ItemsSortWidget(decisions_folder, request, data=sort_data)
        # when no meeting selected in "seance"
        self.assertFalse("seance" in request.form)
        self.assertEqual(sort_widget.query(request.form),
                         {'sort_on': ['linkedMeetingDate', 'sortable_number'],
                          'sort_order': ['descending', 'ascending']})
        meetings = decisions_folder.values()
        request.form["seance"] = meetings[0].UID
        self.assertEqual(sort_widget.query(request.form),
                         {'sort_on': ['sortable_number'],
                          'sort_order': ['ascending']})

    def test_annexes_faceted_criteria(self):
        """The "Annexes?" faceted criterion is only available to institution managers."""
        for faceted_folder in (self.amityville[DEC_FOLDER_ID], self.belleville[DEC_FOLDER_ID]):
            self.login_as_admin()
            criteria = ICriteria(faceted_folder)
            self.assertTrue(criteria.get("annexes"))
            self.logout()
            criteria = ICriteria(faceted_folder)
            self.assertIsNone(criteria.get("annexes"))
