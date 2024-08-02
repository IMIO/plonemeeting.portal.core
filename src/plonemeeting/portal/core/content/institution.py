# -*- coding: utf-8 -*-

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
from plonemeeting.portal.core.config import APP_FOLDER_ID
from plonemeeting.portal.core.config import CATEGORY_IA_DELIB_FIELDS_MAPPING_EXTRA_INCLUDE
from plonemeeting.portal.core.config import DEFAULT_CATEGORY_IA_DELIB_FIELD
from plonemeeting.portal.core.config import PUB_FOLDER_ID
from plonemeeting.portal.core.config import REPRESENTATIVE_IA_DELIB_FIELD
from plonemeeting.portal.core.utils import default_translator
from plonemeeting.portal.core.utils import get_api_url_for_categories
from plonemeeting.portal.core.utils import get_api_url_for_representatives
from plonemeeting.portal.core.widgets.colorselect import ColorSelectFieldWidget
from zope import schema
from zope.interface import implementer
from zope.interface import Interface
from zope.interface import Invalid
from zope.interface import invariant
from zope.schema import ValidationError
from z3c.form.browser.checkbox import CheckBoxFieldWidget

import re
import requests


class InvalidUrlParameters(ValidationError):
    """Exception for invalid url parameters"""

    __doc__ = _(u"Invalid url parameters, the value should start with '&'")


class InvalidColorParameters(ValidationError):
    """Exception for invalid url parameters"""

    __doc__ = _(
        u"Invalid color parameter, the value should be a correct hexadecimal color"
    )


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
        title=_(u"Local category id"),
        vocabulary="plonemeeting.portal.vocabularies.local_categories",
        required=True,
    )
    global_category_id = schema.Choice(
        title=_(u"Global category"),
        vocabulary="plonemeeting.portal.vocabularies.global_categories",
        required=True,
    )


class IUrlParameterRowSchema(Interface):
    parameter = schema.TextLine(
        title=_(u"Parameter"),
        required=True,
        default='extra_include'
    )
    value = schema.TextLine(
        title=_(u"Value"),
        required=True,
    )


class IUrlMeetingFilterParameterRowSchema(Interface):
    parameter = schema.TextLine(
        title=_(u"Parameter"),
        required=True,
        default='review_state'
    )
    value = schema.TextLine(
        title=_(u"Value"),
        required=True,
    )


class IUrlItemFilterParameterRowSchema(Interface):
    parameter = schema.TextLine(
        title=_(u"Parameter"),
        required=True,
        default='listType'
    )
    value = schema.TextLine(
        title=_(u"Value"),
        required=True,
    )


class IRepresentativeMappingRowSchema(Interface):
    representative_key = schema.Choice(title=_(u"Representative key"),
                                       vocabulary="plonemeeting.portal.vocabularies.editable_representative",
                                       required=True)
    representative_value = schema.TextLine(title=_(u"Representative value"),
                                           description=_(u"representative_value_description"),
                                           required=True)
    representative_long_value = schema.TextLine(title=_(u"Representative long values"),
                                                description=_(u"representative_long_value_description"),
                                                required=True)
    active = schema.Bool(title=_(u"Active"), default=True, required=False)


class IInstitution(model.Schema):
    """ Marker interface and Dexterity Python Schema for Institution
    """
    institution_type = schema.Choice(
        title=_(u"Institution Type"),
        vocabulary="plonemeeting.portal.vocabularies.institution_types",
        required=True,
        default="commune"
    )

    directives.widget("enabled_tabs", CheckBoxFieldWidget, multiple='multiple')
    enabled_tabs = schema.List(
        title=_(u"Enabled tabs"),
        value_type=schema.Choice(
            vocabulary="plonemeeting.portal.vocabularies.enabled_tabs"),
        required=True,
        default=[APP_FOLDER_ID, PUB_FOLDER_ID],
    )

    meeting_type = schema.Choice(
        title=_(u"Meeting Type"),
        vocabulary="plonemeeting.portal.vocabularies.meeting_types",
        required=True,
        default="council"
    )

    plonemeeting_url = schema.URI(title=_(u"Plonemeeting URL"), required=False)

    username = schema.TextLine(title=_(u"Username"), required=False)

    password = schema.TextLine(title=_(u"Password"), required=False)

    meeting_config_id = schema.TextLine(title=_(u"Meeting config ID"), required=True, default='meeting-config-council')

    directives.widget(
        "meeting_filter_query",
        DataGridFieldFactory,
        allow_reorder=True,
        auto_append=False,
        display_table_css_class="table table-bordered table-striped")
    meeting_filter_query = schema.List(
        title=_(u"Meeting query filter for list"),
        description=_(u"meeting_filter_query_description"),
        required=True,
        value_type=DictRow(title=u"Parameter name", schema=IUrlMeetingFilterParameterRowSchema),
        default=[{'parameter': 'review_state', 'value': 'created'},
                 {'parameter': 'review_state', 'value': 'frozen'},
                 {'parameter': 'review_state', 'value': 'decided'}]
    )

    directives.widget(
        "item_filter_query",
        DataGridFieldFactory,
        allow_reorder=True,
        auto_append=False,
        display_table_css_class="table table-bordered table-striped")
    item_filter_query = schema.List(
        title=_(u"Published Items query filter"),
        description=_(u"item_filter_query_description"),
        required=True,
        value_type=DictRow(title=u"Parameter name", schema=IUrlItemFilterParameterRowSchema),
        default=[{'parameter': 'listType', 'value': 'normal'},
                 {'parameter': 'listType', 'value': 'late'}]
    )

    directives.widget(
        "item_content_query",
        DataGridFieldFactory,
        allow_reorder=True,
        auto_append=False,
        display_table_css_class="table table-bordered table-striped")
    item_content_query = schema.List(
        title=_(u"Published Items content query"),
        description=_(u"item_content_query_description"),
        required=True,
        value_type=DictRow(title=u"Parameter name", schema=IUrlParameterRowSchema),
        default=[{'parameter': 'extra_include', 'value': 'public_deliberation'}]
    )
    # Formatting fieldset
    model.fieldset(
        "formatting",
        label=_(u"Formatting"),
        fields=[
            "project_decision_disclaimer",
            "item_title_formatting_tal",
            "item_decision_formatting_tal",
            "item_additional_data_formatting_tal",
            "info_annex_formatting_tal",
        ],
    )

    url_rgpd = schema.TextLine(
        title=_(u"Custom page for GDPR text"),
        description=_(u"The url visitors should be redirected to when clicking a GDPR masked text"),
        required=False
    )

    project_decision_disclaimer = RichText(
        title=_(u"Project decision disclaimer"),
        required=False,
        defaultFactory=default_translator(
            _(u"default_in_project_disclaimer", default="")
        ),
    )

    item_title_formatting_tal = schema.TextLine(
        title=_(
            u"Item title formatting tal expression. "
            u"If empty the default title will be used"
        ),
        required=False,
    )

    item_decision_formatting_tal = schema.TextLine(
        title=_(u"Item decision formatting tal expression"),
        required=True,
        default="python: json['extra_include_deliberation']['public_deliberation']",
    )

    item_additional_data_formatting_tal = schema.TextLine(
        title=_(u"Item additional data formatting tal expression"), required=False
    )

    info_annex_formatting_tal = schema.TextLine(
        title=_(u"Info annex formatting tal expression"), required=False
    )

    # Mapping fieldset
    model.fieldset(
        "mapping",
        label=_(u"Mapping"),
        fields=[
            "delib_category_field",
            "categories_mappings",
            "representatives_mappings",
        ],
    )
    delib_category_field = schema.Choice(
        title=_(u"iA.Delib field to use for category mapping"),
        vocabulary="plonemeeting.portal.vocabularies.delib_category_fields",
        required=True,
        default=DEFAULT_CATEGORY_IA_DELIB_FIELD
    )

    directives.widget(
        "categories_mappings",
        DataGridFieldFactory,
        allow_reorder=True,
        auto_append=False,
        display_table_css_class="table table-bordered table-striped")
    categories_mappings = schema.List(
        title=_(u"Categories mappings"),
        description=_(u"categories_mappings_description"),
        value_type=DictRow(title=u"Category mapping", schema=ICategoryMappingRowSchema),
        required=False,
    )

    directives.widget(
        "representatives_mappings",
        DataGridFieldFactory,
        allow_reorder=True,
        auto_append=False,
        display_table_css_class="table table-bordered table-striped")
    representatives_mappings = schema.List(
        title=_(u"Representatives mappings"),
        description=_(u"representatives_mappings_description"),
        value_type=DictRow(
            title=u"Representative mapping", schema=IRepresentativeMappingRowSchema
        ),
        required=False,
    )

    # Styling fieldset
    model.fieldset(
        "style",
        label=_(u"Styling"),
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

    logo = NamedBlobImage(title=_(u"Logo"), required=False)

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


def categories_mappings_invariant(data):
    pass
    mapped_local_category_id = []
    local_category_id_errors = set()
    if data.categories_mappings:
        for row in data.categories_mappings:
            if row['local_category_id'] in mapped_local_category_id:
                local_category_id_errors.add(row['local_category_id'])
            else:
                mapped_local_category_id.append(row['local_category_id'])
        if local_category_id_errors:
            local_category_errors = []
            local_categories = get_vocab(data.__context__, "plonemeeting.portal.vocabularies.local_categories")
            for cat_id in local_category_id_errors:
                local_category_errors.append(local_categories.by_value[cat_id].title)
            local_category_errors = sorted(local_category_errors)
            raise Invalid(_(u'Categories mappings - iA.Delib category mapped more than once : ${categories_title}',
                            mapping={'categories_title': ', '.join(local_category_errors)}))


def representatives_mappings_invariant(data):
    if not data.representatives_mappings:
        return
    new_representatives = data.representatives_mappings
    if new_representatives is None:
        new_representatives = []
    missing_uids = {}
    changes = {}
    for rpz in new_representatives:
        changes[rpz['representative_key']] = rpz['representative_value']
    if data.__context__:
        for rpz in data.__context__.representatives_mappings:
            rpz_uid = rpz['representative_key']
            if rpz_uid not in changes and rpz_uid not in missing_uids:
                brains = api.content.find(portal_type='Item', context=data.__context__, getGroupInCharge=rpz_uid)
                if brains:
                    missing_uids[rpz_uid] = rpz['representative_value']
    if missing_uids:
        raise Invalid(_("Representatives mappings - Removing representatives linked to "
                        "items is not allowed : ${representatives}",
                        mapping={"representatives": ", ".join(missing_uids.values())}))


@implementer(IInstitution)
class Institution(Container):
    """
    """
    def fetch_delib_categories(self):
        delib_config_category_field = CATEGORY_IA_DELIB_FIELDS_MAPPING_EXTRA_INCLUDE[self.delib_category_field]
        url = get_api_url_for_categories(self, delib_config_category_field)
        categories = self._fetch_external_data_for_vocabulary('delib_categories',
                                                              url,
                                                              delib_config_category_field,
                                                              'id',
                                                              'title')
        self.delib_categories = categories

    def fetch_delib_representatives(self):
        representatives = self._fetch_external_data_for_vocabulary('delib_representatives',
                                                                   get_api_url_for_representatives(self),
                                                                   REPRESENTATIVE_IA_DELIB_FIELD,
                                                                   'UID',
                                                                   'title')

        representatives_mappings = self.representatives_mappings or []
        if len(representatives_mappings or []) == 0:
            logger.warning(f"No representatives mappings found for {self.title}")

        for row in representatives_mappings:
            key = row['representative_key']
            if key not in representatives:  # keep history
                representatives[key] = _('Unknown value: ${key}', mapping={'key': key})
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
        return len(self.representatives_mappings) > 0
