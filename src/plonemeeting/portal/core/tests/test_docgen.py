from io import BytesIO

from AccessControl import Unauthorized
from plonemeeting.portal.core.browser.docgen import PMDocumentGenerationView
from plonemeeting.portal.core.tests.portal_test_case import PmPortalDemoFunctionalTestCase
from plonemeeting.portal.core.tests.portal_test_case import PmPortalTestCase
from types import SimpleNamespace
from unittest.mock import patch


class TestPMDocumentGenerationHelperView(PmPortalTestCase):
    def setUp(self):
        super().setUp()
        self.helper = self.portal.restrictedTraverse("@@document-generation-helper-view")

    def test_to_html_link(self):
        html = self.helper.to_html_link("https://plone.org", title="Plone", klass="link")
        self.assertEqual(
            '<a class="link" href="https://plone.org">Plone</a>',
            html,
        )

    def test_uid_url(self):
        item = self.create_object("File")
        expected = f"{self.portal.absolute_url()}/resolveuid/{item.UID()}"
        self.assertEqual(expected, self.helper.uid_url(item))
        helper = item.restrictedTraverse("@@document-generation-helper-view")
        self.assertEqual(expected, helper.uid_url())

    def test_qr_code_calls_barcode(self):
        with patch(
            "plonemeeting.portal.core.browser.docgen.generate_barcode",
            return_value="barcode-url",
        ) as mocked:
            res = self.helper.qr_code("http://example.com", scale=3, secure=1)
            mocked.assert_called_with(
                "http://example.com",
                barcode=58,
                scale=3,
                extra_args=["--secure=1"],
            )
            self.assertEqual("barcode-url", res)

    def test_get_manageable_groups_for_user(self):
        class DummyGroup:
            def __init__(self, gid):
                self._id = gid

            def getId(self):
                return self._id

        groups = [
            DummyGroup("institution-decisions_managers"),
            DummyGroup("institution-staff"),
            DummyGroup("other-publications_managers"),
        ]
        with patch(
            "plonemeeting.portal.core.browser.docgen.api.group.get_groups",
            return_value=groups,
        ), patch(
            "plonemeeting.portal.core.browser.docgen.api.group.get",
            side_effect=lambda gid: DummyGroup(gid),
        ):
            res = self.helper.get_manageable_groups_for_user("john")
        self.assertEqual(
            [g.getId() for g in res],
            [
                "institution-decisions_managers",
                "other-publications_managers",
            ],
        )

    def test_fit_image_size(self):
        tests = [
            ("not_svg", BytesIO(b"PNG"), 2, None),
            ("invalid_svg", BytesIO(b"<svg><rect></svg>"), 1.5, (1.5, 1.5)),
            (
                "viewbox",
                BytesIO(b'<svg viewBox="0 0 100 50"></svg>'),
                10,
                (10.0, 5.0),
            ),
            (
                "width_height",
                BytesIO(b'<svg width="200" height="100"></svg>'),
                10,
                (10.0, 5.0),
            ),
        ]
        for name, img, box, expected in tests:
            with self.subTest(name):
                self.assertEqual(expected, self.helper.fit_image_size(img, box))

    def test_template_logo(self):
        # 1. Institution logo if inside institution and defined
        institution = SimpleNamespace(
            template_logo=SimpleNamespace(data=b"INSTITUTION")
        )
        with patch.object(
            self.helper.utils_view, "is_in_institution", return_value=True
        ), patch.object(
            self.helper.utils_view, "get_current_institution", return_value=institution
        ):
            logo = self.helper.template_logo()
        self.assertIsInstance(logo, BytesIO)
        self.assertEqual(logo.getvalue(), b"INSTITUTION")

        # 2. Site logo from registry if no institution logo for template
        institution = SimpleNamespace(template_logo=None)
        with patch.object(
            self.helper.utils_view, "is_in_institution", return_value=True
        ), patch.object(
            self.helper.utils_view, "get_current_institution", return_value=institution
        ), patch(
            "plonemeeting.portal.core.browser.docgen.api.portal.get_registry_record",
            return_value="dummy",
        ), patch(
            "plonemeeting.portal.core.browser.docgen.b64decode_file",
            return_value=("logo.png", b"SITE"),
        ):
            logo = self.helper.template_logo()
        self.assertIsInstance(logo, BytesIO)
        self.assertEqual(logo.getvalue(), b"SITE")

        # 3. Site logo from registry if not in institution
        with patch.object(
            self.helper.utils_view, "is_in_institution", return_value=False
        ), patch(
            "plonemeeting.portal.core.browser.docgen.api.portal.get_registry_record",
            return_value=None,
        ):
            logo = self.helper.template_logo()
        self.assertIsNone(logo)

class TestPMDocumentGenerationView(PmPortalTestCase):
    def setUp(self):
        super().setUp()
        self.view = self.portal.restrictedTraverse("@@document-generation")

    def test_call_raises_for_anonymous(self):
        self.logout()
        with self.assertRaises(Unauthorized):
            self.view()

    def test_evaluate_expression(self):
        res = self.view._evaluate_expression(
            self.portal,
            "python:extra",
            extra_expr_ctx={"extra": "VALUE"},
        )
        self.assertEqual("VALUE", res)

    def test_prepare_settings_merges_institution_settings(self):
        dummy_pod_template = SimpleNamespace(getId=lambda: "my_template")
        class DummyInstitution:
            def __init__(self):
                self.template_settings = [
                    {"template": "__all__", "setting": "include_qr_code", "expression": "False"},
                    {"template": "__all__", "setting": "include_context_link", "expression": "python:  dummy['foo']"},
                    {
                        "template": "__all__",
                        "setting": "include_expiration_date",
                        "expression": "python: 'lorem ipsum'",
                    },
                    {
                        "template": "__all__",
                        "setting": "im_broken",
                        "expression": "pythn: f'14",
                    },
                    {
                        "template": "__all__",
                        "setting": "im_broken_too",
                        "expression": "python: 1 / 0",
                    },
                ]

        gen_context = {
            "dummy": {"foo": "bar"},
        }
        settings = self.view._prepare_settings(dummy_pod_template, gen_context)
        self.assertEqual(settings["include_qr_code"], True)
        self.assertEqual(settings["include_context_link"], True)
        self.assertEqual(settings["include_expiration_date"], True)

        self.assertEqual(settings["include_publication_text"], True)
        gen_context = {
            "dummy": {"foo": "bar"},
            "institution": DummyInstitution(),
        }
        settings = self.view._prepare_settings(dummy_pod_template, gen_context)
        self.assertEqual(settings["include_qr_code"], False)
        self.assertEqual(settings["include_context_link"], "bar")
        self.assertEqual(settings["include_expiration_date"], 'lorem ipsum')
        self.assertIsNone(settings["im_broken"])
        self.assertIsNone(settings["im_broken_too"])

class TestPMDocumentGenerationViewContext(PmPortalDemoFunctionalTestCase):
    def test_get_generation_context(self):
        view = self.institution.restrictedTraverse("@@document-generation")
        pod_template = SimpleNamespace(getId=lambda: "tpl")
        with patch.object(PMDocumentGenerationView, "_prepare_settings", return_value={"foo": "bar"}):
            ctx = view._get_generation_context(None, pod_template)
        self.assertEqual(ctx["context"], self.institution)
        self.assertEqual(ctx["pod_template"], pod_template)
        self.assertEqual(ctx["settings"], {"foo": "bar"})
        self.assertIn("institution", ctx)
        self.assertEqual(ctx["institution"], self.institution)
