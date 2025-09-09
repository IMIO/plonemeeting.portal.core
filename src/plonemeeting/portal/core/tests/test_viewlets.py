from plone import api
from plone.namedfile.field import NamedBlobImage
from plonemeeting.portal.core.tests.portal_test_case import PmPortalDemoFunctionalTestCase
from plonemeeting.portal.core.viewlets.generationlinks import PMDocumentGeneratorLinksViewlet
from plonemeeting.portal.core.viewlets.logo import PMLogoViewlet
from unittest import mock


class DummyView:
    """Simple view used to instantiate the viewlet."""


class TestPMDocumentGeneratorLinksViewlet(PmPortalDemoFunctionalTestCase):
    def _viewlet(self, context):
        request = self.portal.REQUEST
        return PMDocumentGeneratorLinksViewlet(context, request, DummyView(), None)

    def test_available_requires_authenticated_user_and_templates(self):
        viewlet = self._viewlet(self.item)
        with mock.patch.object(PMDocumentGeneratorLinksViewlet, "get_generable_templates", return_value=[object()]):
            self.assertTrue(viewlet.available())
        self.logout()
        viewlet = self._viewlet(self.item)
        with mock.patch.object(PMDocumentGeneratorLinksViewlet, "get_generable_templates", return_value=[object()]):
            self.assertFalse(viewlet.available())

    def test_get_generable_templates_returns_enabled_templates(self):
        # create a common and an institution template
        self.login_as_admin()
        common_folder = self.portal["config"]["templates"]
        institution_folder = self.institution["templates"]
        common_template = api.content.create(
            container=common_folder,
            type="PODTemplate",
            id="common-template",
            title="Common template",
        )
        institution_template = api.content.create(
            container=institution_folder,
            type="PODTemplate",
            id="institution-template",
            title="Institution template",
        )
        self.login_as_decisions_manager()
        common_template.can_be_generated = mock.Mock(return_value=True)
        institution_template.can_be_generated = mock.Mock(return_value=True)
        self.institution.enabled_templates = [
            common_template.getId(),
            f"{self.institution.getId()}__{institution_template.getId()}",
        ]
        utils_view = mock.Mock()
        utils_view.is_in_institution.return_value = True
        with mock.patch.object(self.item, "restrictedTraverse", return_value=utils_view):
            viewlet = self._viewlet(self.item)
            generable = viewlet.get_generable_templates()
        self.assertListEqual([common_template, institution_template], generable)

    def test_pretty_file_icon(self):
        viewlet = self._viewlet(self.item)
        self.assertDictEqual(
            {"icon": "bi bi-file-earmark-pdf", "color": "bg-red"},
            viewlet.pretty_file_icon("pdf"),
        )
        self.assertEqual(
            {"icon": "bi bi-file-earmark-word", "color": "bg-blue"},
            viewlet.pretty_file_icon("docx"),
        )
        self.assertEqual(
            {"icon": "bi bi-file", "color": "bg-grey"},
            viewlet.pretty_file_icon("toto"),
        )


class TestPMLogoViewlet(PmPortalDemoFunctionalTestCase):

    def _viewlet(self):
        request = self.portal.REQUEST
        return PMLogoViewlet(self.institution, request, DummyView(), None)

    def test_render(self):
        viewlet = self._viewlet()
        viewlet.update()
        self.assertIn(
            """<img alt="Plone site" src="http://nohost/plone/++resource++plone-logo.svg" title="Plone site" />""",
            viewlet.index(),
        )
        self.institution.logo = NamedBlobImage(title="A Nice Logo", required=False)
        viewlet = self._viewlet()
        viewlet.update()
        self.assertIn(
            """<img alt="Amityville" src="http://nohost/plone/amityville/@@images/logo" title="Amityville" />""",
            viewlet.index(),
        )
