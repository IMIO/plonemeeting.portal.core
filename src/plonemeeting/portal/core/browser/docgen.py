import copy
from base64 import b64decode
from io import BytesIO

from AccessControl import Unauthorized
from Products.CMFPlone.utils import getSiteLogo
from collective.behavior.talcondition.utils import evaluateExpressionFor, WRONG_TAL_CONDITION
from collective.documentgenerator.browser.generation_view import DocumentGenerationView
from collective.documentgenerator.helper import DocumentGenerationHelperView
from collective.timestamp.behaviors.timestamp import ITimestampableDocument
from Products.CMFCore.Expression import createExprContext
from Products.CMFCore.Expression import Expression
from plone.formwidget.namedfile.converter import b64decode_file
from plonemeeting.portal.core import logger
from imio.helpers.barcode import generate_barcode
from plone import api
from asn1crypto import tsp, cms, x509
from html import escape
from zope.i18n import translate
from plonemeeting.portal.core import _


class PMDocumentGenerationHelperView(DocumentGenerationHelperView):
    """Helper view for document generation."""

    def __init__(self, context, request):
        super().__init__(context, request)
        self.utils_view = self.context.restrictedTraverse("@@utils_view")

    def qr_code(self, url, scale=2, secure=2):
        """
        Returns a QR code image URL for the timestamp.
        """
        return generate_barcode(
            url,
            barcode=58,
            scale=scale,
            extra_args=[f"--secure={secure}"],
        )

    def to_html_link(self, url, title=None, klass=""):
        """
        Returns a HTML link URL.
        """
        return f'<a class="{klass}" href="{escape(url)}">{title if title else url}</a>'

    def uid_url(self, obj=None):
        portal = api.portal.get()
        if obj is None:
            obj = self.context
        return f"{portal.absolute_url()}/resolveuid/{obj.UID()}"

    def template_logo(self):
        """Return the institution logo (BytesIO) or fall back to the site logo."""
        # 1) Institution logo
        if self.utils_view.is_in_institution():
            institution = self.utils_view.get_current_institution()
            if institution.template_logo:
                return BytesIO(institution.template_logo.data)
        # 2) Site logo from registry if no institution logo for template
        site_logo = api.portal.get_registry_record("plone.site_logo")
        if site_logo:
            filename, data = b64decode_file(site_logo)
            return BytesIO(data)
        return None

    def template_logo_size(self):
        """Return the institution logo size as a tuple (width, height)."""
        if self.utils_view.is_in_institution():
            institution = self.utils_view.get_current_institution()
            if institution.template_logo:
                # todo clamp to a max template logo size
                pass
        site_logo = api.portal.get_registry_record("plone.site_logo")
        if site_logo:
            filename, data = b64decode_file(site_logo)
            return BytesIO(data)

        return getSiteLogo()

    def get_manageable_groups_for_user(self, username):
        """
        Return only 'institution groups' for this user, i.e.,
        groups that match typical institution naming patterns.
        """
        all_user_groups = api.group.get_groups(username=username)
        # We'll say any group ID that ends (or contains) these strings is an 'institution group'
        # Adjust to match your actual naming convention.
        manageable_institution_suffixes = ("decisions_managers", "publications_managers", "managers")
        user_manageable_groups = []
        for group in all_user_groups:
            group_id = group.getId()
            # Keep only groups that are institution-related
            if any(suffix in group_id for suffix in manageable_institution_suffixes):
                user_manageable_groups.append(api.group.get(group_id))
        return user_manageable_groups

class PMDocumentGenerationView(DocumentGenerationView):
    """Redefine the DocumentGenerationView to extend context available in the template
    and to handle POD templates sent to mailing lists."""

    def __call__(self, template_uid="", output_format="", **kwargs):
        if api.user.is_anonymous():
            raise Unauthorized("You need to be logged in to generate documents.")
        return super().__call__(template_uid, output_format, **kwargs)

    def _evaluate_expression(
        self,
        obj,
        expression,
        extra_expr_ctx={},
        raise_on_error=False,
    ):
        """Evaluate given TAL expression extending expression context with p_extra_expr_ctx."""
        portal = api.portal.get()
        ctx = createExprContext(obj.aq_inner.aq_parent, portal, obj)
        for extra_key, extra_value in list(extra_expr_ctx.items()):
            ctx.setGlobal(extra_key, extra_value)

        if raise_on_error:
            res = Expression(expression)(ctx)
        else:
            try:
                res = Expression(expression)(ctx)
            except Exception as e:
                logger.warn(WRONG_TAL_CONDITION.format(expression, obj.absolute_url(), str(e)))
                res = None
        return res

    def _prepare_settings(self, pod_template, gen_context=None):
        settings = copy.deepcopy(
            api.portal.get_registry_record(name="plonemeeting.portal.core.template_default_settings")
        )
        # First, we'll merge the institution settings with the defaults
        if "institution" in gen_context:
            institution_settings = gen_context["institution"].template_settings
            for row in institution_settings:
                if row["template"] == "__all__" or row["template"] == pod_template.getId():
                    settings[row["setting"]] = row["expression"]

        # Then, we'll evaluate all expressions to have the final settings
        for setting, tal_expr in settings.items():
            settings[setting] = self._evaluate_expression(
                self.context,
                tal_expr,
                extra_expr_ctx=gen_context,
            )
        return settings

    def _get_generation_context(self, helper_view, pod_template):
        """ """
        view = self.context.restrictedTraverse("@@document-generation-helper-view")
        utils_view = self.context.restrictedTraverse("@@utils_view")
        user = api.user.get_current()
        specific_context = {
            "self": self.context,
            "context": self.context,
            "view": view,
            "member": user,
            "pod_template": pod_template,
            "utils": utils_view,
            "user": user,
            "portal": api.portal.get(),
            "site_url": api.portal.get().absolute_url(),
        }
        if utils_view.is_in_institution():
            specific_context["institution"] = utils_view.get_current_institution()

        settings = self._prepare_settings(pod_template, specific_context)
        specific_context["settings"] = settings

        if ITimestampableDocument.providedBy(self.context):
            specific_context["timestamp_utils"] = self.context.restrictedTraverse("@@timestamp-info")

        return specific_context
