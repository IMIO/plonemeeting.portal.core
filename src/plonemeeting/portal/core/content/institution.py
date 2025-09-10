# -*- coding: utf-8 -*-
from collective.z3cform.datagridfield.blockdatagridfield import BlockDataGridFieldFactory
from collective.z3cform.datagridfield.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield.row import DictRow
from copy import deepcopy
from imio.helpers.content import get_vocab
from plone import api
from plone.app.textfield import RichText
from plone.autoform import directives
from plone.dexterity.content import Container
from plone.namedfile.field import NamedBlobImage
from plone.supermodel import model
from plonemeeting.portal.core import _
from plonemeeting.portal.core import logger
from plonemeeting.portal.core.config import API_HEADERS
from plonemeeting.portal.core.config import CATEGORY_IA_DELIB_FIELDS_MAPPING_EXTRA_INCLUDE
from plonemeeting.portal.core.config import DEC_FOLDER_ID
from plonemeeting.portal.core.config import DEFAULT_CATEGORY_IA_DELIB_FIELD
from plonemeeting.portal.core.config import PUB_FOLDER_ID
from plonemeeting.portal.core.config import REPRESENTATIVE_IA_DELIB_FIELD
from plonemeeting.portal.core.utils import default_translator
from plonemeeting.portal.core.utils import get_api_url_for_categories
from plonemeeting.portal.core.utils import get_api_url_for_representatives
from plonemeeting.portal.core.utils import get_members_group_id
from plonemeeting.portal.core.utils import get_publication_reviewers_group_id
from plonemeeting.portal.core.widgets.colorselect import ColorSelectFieldWidget
from plonemeeting.portal.core.widgets.image import PMNamedImageFieldWidget
from Products.CMFCore.utils import getToolByName
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from zope import schema
from zope.interface import implementer
from zope.interface import Interface
from zope.interface import Invalid
from zope.interface import invariant
from zope.schema import ValidationError
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

import re
import requests


class InvalidUrlParameters(ValidationError):
    """Exception for invalid url parameters"""

    __doc__ = _("Invalid url parameters, the value should start with '&'")


class InvalidColorParameters(ValidationError):
    """Exception for invalid url parameters"""

    __doc__ = _("Invalid color parameter, the value should be a correct hexadecimal color")


def validate_url_parameters(value):
    """Validate if the url parameters"""
    if value and value[0] != "&":
        raise InvalidUrlParameters(value)
    return True


def validate_color_parameters(value):
    """Validate if the value is a correct hex color parameter"""
    is_hexadecimal_color = re.search(r"^#(?:[0-9a-fA-F]{3}){1,2}$", value)
    if not is_hexadecimal_color:
        raise InvalidColorParameters()
    else:
        return True


class ICategoryMappingRowSchema(Interface):
    local_category_id = schema.Choice(
        title=_("Local category id"),
        vocabulary="plonemeeting.portal.vocabularies.local_categories",
        required=True,
    )
    global_category_id = schema.Choice(
        title=_("Global category"),
        vocabulary="plonemeeting.portal.vocabularies.global_categories",
        required=True,
    )


class IUrlParameterRowSchema(Interface):
    parameter = schema.TextLine(title=_("Parameter"), required=True, default="extra_include")
    value = schema.TextLine(
        title=_("Value"),
        required=True,
    )


class IUrlMeetingFilterParameterRowSchema(Interface):
    parameter = schema.TextLine(title=_("Parameter"), required=True, default="review_state")
    value = schema.TextLine(
        title=_("Value"),
        required=True,
    )


class IUrlItemFilterParameterRowSchema(Interface):
    parameter = schema.TextLine(title=_("Parameter"), required=True, default="listType")
    value = schema.TextLine(
        title=_("Value"),
        required=True,
    )


class IRepresentativeMappingRowSchema(Interface):
    representative_key = schema.Choice(
        title=_("Representative key"),
        vocabulary="plonemeeting.portal.vocabularies.editable_representative",
        required=True,
    )
    representative_value = schema.TextLine(
        title=_("Representative value"), description=_("representative_value_description"), required=True
    )
    representative_long_value = schema.TextLine(
        title=_("Representative long values"), description=_("representative_long_value_description"), required=True
    )
    active = schema.Bool(title=_("Active"), default=True, required=False)


class ITemplateSettingsRowSchema(Interface):
    template = schema.Choice(
        title=_("Template"),
        vocabulary="plonemeeting.portal.institution_all_and_templates_vocabulary",
        required=True,
    )
    setting = schema.Choice(
        title=_("Setting"),
        description=_("Setting to configure. The value between brackets is the technical name used in the templates."),
        vocabulary="plonemeeting.portal.institution_template_settings_vocabulary",
        required=True,
    )
    expression = schema.TextLine(
        title=_("TAL expression"),
        description=_(
            "Enter a TAL expression that once evaluated will return the setting's value. Elements context, request, view, template, utils, portal, site_url, user are available for the expression."
        ),
        required=False,
        default="",
    )


class IInstitution(model.Schema):
    """Marker interface and Dexterity Python Schema for Institution"""

    institution_type = schema.Choice(
        title=_("Institution Type"),
        vocabulary="plonemeeting.portal.vocabularies.institution_types",
        required=True,
        default="commune",
    )

    directives.widget("enabled_tabs", CheckBoxFieldWidget, multiple="multiple")
    enabled_tabs = schema.List(
        title=_("Enabled tabs"),
        value_type=schema.Choice(vocabulary="plonemeeting.portal.vocabularies.enabled_tabs"),
        required=True,
        default=[DEC_FOLDER_ID, PUB_FOLDER_ID],
    )

    meeting_type = schema.Choice(
        title=_("Meeting Type"),
        vocabulary="plonemeeting.portal.vocabularies.meeting_types",
        required=True,
        default="council",
    )

    plonemeeting_url = schema.URI(title=_("Plonemeeting URL"), required=False)

    username = schema.TextLine(title=_("Username"), required=False)

    password = schema.TextLine(title=_("Password"), required=False)

    meeting_config_id = schema.TextLine(title=_("Meeting config ID"), required=True, default="meeting-config-council")

    directives.widget(
        "meeting_filter_query",
        DataGridFieldFactory,
        allow_reorder=True,
        auto_append=False,
        display_table_css_class="table table-bordered table-striped",
    )
    meeting_filter_query = schema.List(
        title=_("Meeting query filter for list"),
        description=_("meeting_filter_query_description"),
        required=True,
        value_type=DictRow(title="Parameter name", schema=IUrlMeetingFilterParameterRowSchema),
        default=[
            {"parameter": "review_state", "value": "created"},
            {"parameter": "review_state", "value": "frozen"},
            {"parameter": "review_state", "value": "decided"},
        ],
    )

    directives.widget(
        "item_filter_query",
        DataGridFieldFactory,
        allow_reorder=True,
        auto_append=False,
        display_table_css_class="table table-bordered table-striped",
    )
    item_filter_query = schema.List(
        title=_("Published Items query filter"),
        description=_("item_filter_query_description"),
        required=True,
        value_type=DictRow(title="Parameter name", schema=IUrlItemFilterParameterRowSchema),
        default=[{"parameter": "listType", "value": "normal"}, {"parameter": "listType", "value": "late"}],
    )

    directives.widget(
        "item_content_query",
        DataGridFieldFactory,
        allow_reorder=True,
        auto_append=False,
        display_table_css_class="table table-bordered table-striped",
    )
    item_content_query = schema.List(
        title=_("Published Items content query"),
        description=_("item_content_query_description"),
        required=True,
        value_type=DictRow(title="Parameter name", schema=IUrlParameterRowSchema),
        default=[{"parameter": "extra_include", "value": "public_deliberation"}],
    )
    # Formatting fieldset
    model.fieldset(
        "formatting",
        label=_("Formatting"),
        fields=[
            "project_decision_disclaimer",
            "item_title_formatting_tal",
            "item_decision_formatting_tal",
            "item_additional_data_formatting_tal",
            "info_annex_formatting_tal",
        ],
    )

    url_rgpd = schema.TextLine(
        title=_("Custom page for GDPR text"),
        description=_("The url visitors should be redirected to when clicking a GDPR masked text"),
        required=False,
    )

    project_decision_disclaimer = RichText(
        title=_("Project decision disclaimer"),
        required=False,
        defaultFactory=default_translator(_("default_in_project_disclaimer", default="")),
    )

    item_title_formatting_tal = schema.TextLine(
        title=_("Item title formatting tal expression. " "If empty the default title will be used"),
        required=False,
    )

    item_decision_formatting_tal = schema.TextLine(
        title=_("Item decision formatting tal expression"),
        required=True,
        default="python: json['extra_include_deliberation']['public_deliberation']",
    )

    item_additional_data_formatting_tal = schema.TextLine(
        title=_("Item additional data formatting tal expression"), required=False
    )

    info_annex_formatting_tal = schema.TextLine(title=_("Info annex formatting tal expression"), required=False)

    webstats_js = schema.SourceText(
        title=_("JavaScript integrations"),
        description=_(
            "For enabling third-party JavaScript integrations "
            "from external providers (e.g. Google "
            "Analytics). Paste the provided code snippet here. "
            "It will be rendered as "
            "entered near the end of the page."
        ),
        default="",
        required=False,
    )

    # Mapping fieldset
    model.fieldset(
        "mapping",
        label=_("Mapping"),
        fields=[
            "delib_category_field",
            "categories_mappings",
            "representatives_mappings",
        ],
    )
    delib_category_field = schema.Choice(
        title=_("iA.Delib field to use for category mapping"),
        vocabulary="plonemeeting.portal.vocabularies.delib_category_fields",
        required=True,
        default=DEFAULT_CATEGORY_IA_DELIB_FIELD,
    )

    directives.widget(
        "categories_mappings",
        DataGridFieldFactory,
        allow_reorder=True,
        auto_append=False,
        display_table_css_class="table table-bordered table-striped",
    )
    categories_mappings = schema.List(
        title=_("Categories mappings"),
        description=_("categories_mappings_description"),
        value_type=DictRow(title="Category mapping", schema=ICategoryMappingRowSchema),
        required=False,
    )

    directives.widget(
        "representatives_mappings",
        DataGridFieldFactory,
        allow_reorder=True,
        auto_append=False,
        display_table_css_class="table table-bordered table-striped",
    )
    representatives_mappings = schema.List(
        title=_("Representatives mappings"),
        description=_("representatives_mappings_description"),
        value_type=DictRow(title="Representative mapping", schema=IRepresentativeMappingRowSchema),
        required=False,
    )

    # Publications fieldset
    model.fieldset(
        "publications",
        label=_("Publications"),
        fields=[
            "publications_power_users",
        ],
    )

    directives.widget("publications_power_users", CheckBoxFieldWidget, multiple="multiple")
    publications_power_users = schema.List(
        title=_("Power users"),
        description=_("power_users_description"),
        value_type=schema.Choice(vocabulary="plonemeeting.portal.vocabularies.publications_power_users"),
        required=True,
    )

    # Styling fieldset
    model.fieldset(
        "style",
        label=_("Styling"),
        fields=[
            "logo",
            "header_color",
            "nav_color",
            "nav_text_color",
            "links_color",
            "footer_color",
            "footer_text_color",
        ],
    )
    directives.widget("logo", PMNamedImageFieldWidget)
    logo = NamedBlobImage(title=_("Logo"), required=False)

    directives.widget("header_color", ColorSelectFieldWidget)
    header_color = schema.TextLine(
        title=_("Header color"),
        required=True,
        default="#ffffff",
        constraint=validate_color_parameters,
    )

    directives.widget("nav_color", ColorSelectFieldWidget)
    nav_color = schema.TextLine(
        title=_("Navigation bar color"),
        required=True,
        default="#007bb1",  # Plone blue
        constraint=validate_color_parameters,
    )

    directives.widget("nav_text_color", ColorSelectFieldWidget)
    nav_text_color = schema.TextLine(
        title=_("Navigation bar text color"),
        required=True,
        default="#ffffff",
        constraint=validate_color_parameters,
    )

    directives.widget("links_color", ColorSelectFieldWidget)
    links_color = schema.TextLine(
        title=_("Links text color"),
        required=True,
        default="#007bb1",
        constraint=validate_color_parameters,
    )

    directives.widget("footer_color", ColorSelectFieldWidget)
    footer_color = schema.TextLine(
        title=_("Footer color"),
        required=True,
        default="#2e3133",
        constraint=validate_color_parameters,
    )

    directives.widget("footer_text_color", ColorSelectFieldWidget)
    footer_text_color = schema.TextLine(
        title=_("Footer text color"),
        required=True,
        default="#cccccc",
        constraint=validate_color_parameters,
    )

    @invariant
    def institution_invariant(data):
        categories_mappings_invariant(data)
        representatives_mappings_invariant(data)

    # Documents fieldset
    model.fieldset(
        "templates",
        label=_("Templates"),
        fields=[
            "enabled_templates",
            "template_logo",
            "template_settings",
        ],
    )
    enabled_templates = schema.List(
        title=_("Activated templates"),
        description=_("enabled_templates_description"),
        value_type=schema.Choice(vocabulary="plonemeeting.portal.institution_templates_vocabulary"),
        required=False,
        default=[],
    )
    directives.widget("template_logo", PMNamedImageFieldWidget)
    template_logo = NamedBlobImage(title=_("Template logo"), required=False)

    directives.widget(
        "template_settings",
        BlockDataGridFieldFactory,
        allow_reorder=True,
        auto_append=False,
        display_table_css_class="table table-bordered table-striped",
    )
    template_settings = schema.List(
        title=_("Template settings"),
        description=_("Template settings used to customize templates. Leave empty to use default values."),
        value_type=DictRow(
            title="tablerow",
            schema=ITemplateSettingsRowSchema,
        ),
    )


def categories_mappings_invariant(data):
    mapped_local_category_id = []
    local_category_id_errors = set()
    if data.categories_mappings:
        for row in data.categories_mappings:
            if row["local_category_id"] in mapped_local_category_id:
                local_category_id_errors.add(row["local_category_id"])
            else:
                mapped_local_category_id.append(row["local_category_id"])
        if local_category_id_errors:
            local_category_errors = []
            local_categories = get_vocab(data.__context__, "plonemeeting.portal.vocabularies.local_categories")
            for cat_id in local_category_id_errors:
                local_category_errors.append(local_categories.by_value[cat_id].title)
            local_category_errors = sorted(local_category_errors)
            raise Invalid(
                _(
                    "Categories mappings - iA.Delib category mapped more than once : ${categories_title}",
                    mapping={"categories_title": ", ".join(local_category_errors)},
                )
            )


def representatives_mappings_invariant(data):
    if not data.representatives_mappings:
        return
    new_representatives = data.representatives_mappings
    if new_representatives is None:
        new_representatives = []
    missing_uids = {}
    changes = {}
    for rpz in new_representatives:
        changes[rpz["representative_key"]] = rpz["representative_value"]
    if data.__context__ and data.__context__.representatives_mappings:
        for rpz in data.__context__.representatives_mappings:
            rpz_uid = rpz["representative_key"]
            if rpz_uid not in changes and rpz_uid not in missing_uids:
                brains = api.content.find(portal_type="Item", context=data.__context__, getGroupInCharge=rpz_uid)
                if brains:
                    missing_uids[rpz_uid] = rpz["representative_value"]
    if missing_uids:
        raise Invalid(
            _(
                "Representatives mappings - Removing representatives linked to "
                "items is not allowed : ${representatives}",
                mapping={"representatives": ", ".join(missing_uids.values())},
            )
        )


@implementer(IInstitution)
class Institution(Container):
    """ """

    def fetch_delib_categories(self):
        delib_config_category_field = CATEGORY_IA_DELIB_FIELDS_MAPPING_EXTRA_INCLUDE[self.delib_category_field]
        url = get_api_url_for_categories(self, delib_config_category_field)
        categories = self._fetch_external_data_for_vocabulary(
            "delib_categories", url, delib_config_category_field, "id", "title"
        )
        self.delib_categories = categories

    def fetch_delib_representatives(self):
        representatives = self._fetch_external_data_for_vocabulary(
            "delib_representatives",
            get_api_url_for_representatives(self),
            REPRESENTATIVE_IA_DELIB_FIELD,
            "UID",
            "title",
        )

        representatives_mappings = self.representatives_mappings or []
        if len(representatives_mappings or []) == 0:
            logger.warning(f"No representatives mappings found for {self.title}")

        for row in representatives_mappings:
            key = row["representative_key"]
            if key not in representatives:  # keep history
                representatives[key] = _("Unknown value: ${key}", mapping={"key": key})
        self.delib_representatives = representatives

    def _fetch_external_data_for_vocabulary(self, attr_name, url, url_extra_include, json_voc_value, json_voc_title):
        # ensure empty dict if None or attr doesn't exist
        res = deepcopy(getattr(self, attr_name, {})) or {}
        if self.plonemeeting_url and self.meeting_config_id and self.username and self.password:
            if url:
                logger.info("Fetching {} for {} [Start]".format(attr_name, self.title))
                try:
                    response = requests.get(url, auth=(self.username, self.password), headers=API_HEADERS)
                    if response.status_code in (200, 201):
                        res = {}
                        json = response.json()
                        values_json = json["extra_include_{}".format(url_extra_include)]
                        for value in values_json:
                            res[value[json_voc_value]] = value[json_voc_title]
                        logger.info("Fetching {} for {} [End]".format(attr_name, self.title))
                    else:
                        logger.error("Unable to fetch {}, error is {} [End]".format(attr_name, response.content))
                except requests.exceptions.ConnectionError as err:
                    logger.warning("Error while trying to connect to iA.Delib", exc_info=err)
                    api.portal.show_message(_("Webservice connection error !"), request=self.REQUEST, type="warning")
        return res

    def is_representatives_mapping_used(self):
        """Check if this config is using the representatives in charge feature"""
        return bool(self.representatives_mappings)

    def get_all_institution_users(self):
        """Return members belonging to any group whose name starts with institution_id."""
        group_tool = getToolByName(self, "portal_groups")
        membership_tool = getToolByName(self, "portal_membership")

        group_id = get_members_group_id(self)
        group = group_tool.getGroupById(group_id)
        if not group:
            # The group doesn't exist, it shouldn't happen
            return []

        user_ids = [user.id for user in group.getGroupMembers()]
        members = [membership_tool.getMemberById(uid) for uid in user_ids if membership_tool.getMemberById(uid)]
        return sorted(members, key=lambda x: x.id)

    def has_publications_reviewers(self):
        """Check if the institution has at least one publication validator."""
        group_tool = getToolByName(self, "portal_groups")
        group_id = get_publication_reviewers_group_id(self)
        group = group_tool.getGroupById(group_id)
        if not group:
            return False
        return bool(group.getGroupMembers())
