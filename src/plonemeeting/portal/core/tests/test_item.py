# -*- coding: utf-8 -*-
from imio.helpers.content import richtextval
from plone import api
from plonemeeting.portal.core.content.item import get_pretty_representatives
from plonemeeting.portal.core.tests.portal_test_case import IMG_BASE64_DATA
from plonemeeting.portal.core.tests.portal_test_case import PmPortalDemoFunctionalTestCase


class TestItemView(PmPortalDemoFunctionalTestCase):
    def setUp(self):
        super().setUp()
        self.amityville = self.portal["belleville"]
        self.meeting = self.amityville["16-novembre-2018-08-30"]
        self.project_meeting = self.amityville["16-novembre-2018-08-30"]
        self.item = self.meeting["approbation-du-pv-du-xxx"]
        self.login_as_test()

    def test_item_view(self):
        # when meeting is in decision
        self.assertEqual(api.content.get_state(self.meeting), "decision")
        view = self.item.restrictedTraverse("@@view")
        self.assertTrue(view())
        # when meeting is in decision
        self.login_as_manager()
        api.content.transition(self.meeting, to_state="in_project")
        self.assertEqual(api.content.get_state(self.meeting), "in_project")
        view = self.item.restrictedTraverse("@@view")
        self.assertTrue(view())

    def test_get_files(self):
        files = self.item.restrictedTraverse("@@view").get_files()
        self.assertEqual(1, len(files))
        self.assertEqual(self.item["document.pdf"], files[0].getObject())

    def test_title(self):
        delattr(self.item, "_formatted_title")
        self.assertEqual(self.item.formatted_title, None)
        self.assertEqual(self.item.title, "Approbation du PV du XXX")
        self.item.formatted_title = richtextval("<p>test formatted title</p>")
        self.assertEqual(self.item.title, "test formatted title")

    def test_get_pretty_representatives(self):
        self.assertEqual(get_pretty_representatives(self.item)(), "Mme LOREM")

        self.item.representatives_in_charge = ["Yololololo-lolo-lolololo"]
        self.assertRaises(AttributeError, get_pretty_representatives(self.item))

        self.item.representatives_in_charge = [
            "a2396143f11f4e2292f12ee3b3447739",
            "7a82fee367a0416f8d7e8f4a382db0d1",
            "f3f9e7808ddb4e56946b2dba6370eb9b",
            "bf5fccd9bc9048e9957680c7ab5576b4",
        ]
        self.assertEqual(
            get_pretty_representatives(self.item)(),
            "Mme Ipsum, Mme LOREM, Mr Bara, Mr Wara",
        )

        self.item.representatives_in_charge = [
            "bf5fccd9bc9048e9957680c7ab5576b4",
            "7a82fee367a0416f8d7e8f4a382db0d1",
            "a2396143f11f4e2292f12ee3b3447739",
            "7a82fee367a0416f8d7e8f4a382db0d1",
            "f3f9e7808ddb4e56946b2dba6370eb9b",
            "bf5fccd9bc9048e9957680c7ab5576b4",
        ]
        self.assertEqual(
            get_pretty_representatives(self.item)(),
            "Mr Wara, Mme LOREM, Mme Ipsum, Mr Bara",
        )

    def test_decision_with_images(self):
        pattern = '<p>Text with image <img src="{0}"/> and more text.</p>'
        text = pattern.format(IMG_BASE64_DATA)
        self.item.decision = richtextval(text)
        self.assertEqual(self.item.decision.output, text)
        # a part from data:image, other elements are still removed
        text = "<p>Text.</p><script>nasty();</script>"
        self.item.decision = richtextval(text)
        self.assertEqual(self.item.decision.output, "<p>Text.</p>")
