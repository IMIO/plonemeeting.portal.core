# -*- coding: utf-8 -*-
from collective.z3cform.datagridfield.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield.row import DictRow
from imio.helpers.content import get_vocab
from plone.app.textfield import RichText
from plone.autoform import directives
from plone.dexterity.content import Container
from plone.namedfile.field import NamedBlobImage
from plone.supermodel import model
from plonemeeting.portal.core import _
from plonemeeting.portal.core import logger
from plonemeeting.portal.core.config import API_HEADERS
from plonemeeting.portal.core.config import CATEGORY_IA_DELIB_FIELDS_MAPPING_EXTRA_INCLUDE
from plonemeeting.portal.core.config import DEFAULT_CATEGORY_IA_DELIB_FIELD
from plonemeeting.portal.core.utils import default_translator
from plonemeeting.portal.core.utils import get_api_url_for_categories
from plonemeeting.portal.core.widgets.colorselect import ColorSelectFieldWidget
from zope import schema
from zope.interface import implementer
from zope.interface import Interface
from zope.interface import Invalid
from zope.interface import invariant
from zope.schema import ValidationError

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


class IRepresentativeMappingRowSchema(Interface):
    representative_key = schema.TextLine(title=_(u"Representative key"),
                                         description=_(u"representative_key_description"))
    representative_value = schema.TextLine(title=_(u"Representative value"),
                                           description=_(u"representative_value_description"))
    representative_long_value = schema.TextLine(title=_(u"Representative long values"),
                                                description=_(u"representative_long_value_description"))
    active = schema.Bool(title=_(u"Active"), default=True)


class IInstitution(model.Schema):
    """ Marker interface and Dexterity Python Schema for Institution
    """
    plonemeeting_url = schema.URI(title=_(u"Plonemeeting URL"), required=False)

    username = schema.TextLine(title=_(u"Username"), required=False)

    password = schema.TextLine(title=_(u"Password"), required=False)

    meeting_config_id = schema.TextLine(title=_(u"Meeting config ID"), required=True, default='meeting-config-council')

    project_decision_disclaimer = RichText(
        title=_(u"Project decision disclaimer"),
        required=False,
        defaultFactory=default_translator(
            _(u"default_in_project_disclaimer", default="")
        ),
    )

    additional_meeting_query_string_for_list = schema.TextLine(
        title=_(u"Additional Meeting query string for list"),
        description=_(u"additional_meeting_query_string_for_list_description"),
        required=True,
        constraint=validate_url_parameters,
        default="&review_state=frozen&review_state=decided"
    )

    additional_published_items_query_string = schema.TextLine(
        title=_(u"Additional Published Items query string"),
        description=_(u"additional_published_items_query_string_description"),
        required=True,
        constraint=validate_url_parameters,
        default="&review_state=itemfrozen&review_state=accepted&review_state=accepted_but_modified"
    )
    # Formatting fieldset
    model.fieldset(
        "formatting",
        label=_(u"Formatting"),
        fields=[
            "item_title_formatting_tal",
            "item_decision_formatting_tal",
            "item_additional_data_formatting_tal",
            "info_annex_formatting_tal",
        ],
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
        default="python: json['decision']['data']",
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

    directives.widget("categories_mappings", DataGridFieldFactory, allow_reorder=True)
    categories_mappings = schema.List(
        title=_(u"Categories mappings"),
        description=_(u"categories_mappings_description"),
        value_type=DictRow(title=u"Category mapping", schema=ICategoryMappingRowSchema),
        required=False,
    )

    directives.widget("representatives_mappings", DataGridFieldFactory, allow_reorder=True)
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
    def categories_mappings_invariant(data):
        mapped_local_category_id = []
        local_category_id_errors = set()
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
            raise Invalid(_(u'iA.Delib category mapped more than once : ${categories_title}',
                            mapping={'categories_title': ', '.join(local_category_errors)}))


@implementer(IInstitution)
class Institution(Container):
    """
    """
    def fetch_delib_categories(self):
        categories = []
        if self.plonemeeting_url and self.meeting_config_id and self.username and self.password:
            delib_config_category_field = CATEGORY_IA_DELIB_FIELDS_MAPPING_EXTRA_INCLUDE[
                self.delib_category_field]
            url = get_api_url_for_categories(self, delib_config_category_field)
            if url:
                logger.info("Fetching delib categories for {} [Start]".format(self.title))
                response = requests.get(
                    url, auth=(self.username, self.password), headers=API_HEADERS
                )
                if response.status_code in (200, 201):
                    delib_config_category_field = CATEGORY_IA_DELIB_FIELDS_MAPPING_EXTRA_INCLUDE[
                        self.delib_category_field]
                    json = response.json()
                    cat_json = json["extra_include_{categories}".format(
                        categories=delib_config_category_field)]

                    for cat in cat_json:
                        categories.append((cat['id'], cat['title']))
                    self.delib_categories = categories
                    logger.info("Fetching delib categories for {} [End]".format(self.title))
                else:
                    logger.error("Unable to fetch categories, error is {} [End]".format(
                        response.content))
        return categories
