from plone.api.portal import set_registry_record
from plone.app.testing import logout
from plonemeeting.portal.core.tests.portal_test_case import PmPortalTestCase


class TestContactForm(PmPortalTestCase):
    def setUp(self):
        super().setUp()
        self.ci_view = self.portal.restrictedTraverse("contact-info")
        set_registry_record("plone.email_from_address", "test@test.com")
        set_registry_record("plone.email_from_name", "Test user")

    def test_valid_mail_config(self):
        self.assertNotIn("This site doesn't have a valid email setup", self.ci_view())

    def test_render_correctly(self):
        self.assertIn(
            '<h1 class="documentFirstHeading">' "Contact form" "</h1>", self.ci_view()
        )
        self.assertIn(
            '<div class="documentDescription">'
            "Fill in this form to contact the site owners."
            "</div>",
            self.ci_view(),
        )
        self.assertIn(
            '<textarea name="form.widgets.message" id="form-widgets-message"',
            self.ci_view(),
        )

    def test_accessible_by_anonymous(self):
        logout()
        self.assertIn(
            '<textarea name="form.widgets.message" id="form-widgets-message"',
            self.ci_view(),
        )

    def test_has_captcha_field(self):
        self.assertIn('id="formfield-form-widgets-captcha"', self.ci_view())
