# -*- coding: utf-8 -*-
import re

from collective.z3cform.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield import DictRow
from plone.app.textfield import RichText
from plone.dexterity.browser import add
from plone.dexterity.browser import edit
from plone.dexterity.content import Container
from plone.autoform import directives
from plone.namedfile.field import NamedBlobImage
from plone.supermodel import model
from zope import schema
from zope.interface import Interface
from zope.interface import implementer
from zope.schema import ValidationError

from plonemeeting.portal.core import _
from plonemeeting.portal.core.utils import default_translator
from plonemeeting.portal.core.widgets.colorselect import ColorSelectFieldWidget


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
    local_category_id = schema.TextLine(title=_(u"Local category id"))
    global_category_id = schema.Choice(
        title=_(u"Global category"),
        vocabulary="plonemeeting.portal.vocabularies.global_categories",
        required=True,
    )


class IRepresentativeMappingRowSchema(Interface):
    representative_key = schema.TextLine(title=_(u"Representative key"))
    representative_value = schema.TextLine(title=_(u"Representative value"))
    representative_long_value = schema.TextLine(title=_(u"Representative long values"))
    active = schema.Bool(title=_(u"Active"), default=True)


class IInstitution(model.Schema):
    """ Marker interface and Dexterity Python Schema for Institution
    """

    plonemeeting_url = schema.URI(title=_(u"Plonemeeting URL"), required=False)

    username = schema.TextLine(title=_(u"Username"), required=False)

    password = schema.TextLine(title=_(u"Password"), required=False)

    meeting_config_id = schema.TextLine(title=_(u"Meeting config ID"), required=False)

    project_decision_disclaimer = RichText(
        title=_(u"Project decision disclaimer"),
        required=False,
        defaultFactory=default_translator(
            _(u"default_in_project_disclaimer", default="")
        ),
    )

    additional_meeting_query_string_for_list = schema.TextLine(
        title=_(u"Additional Meeting query string for list"),
        required=False,
        constraint=validate_url_parameters,
    )

    additional_published_items_query_string = schema.TextLine(
        title=_(u"Additional Published Items query string"),
        required=False,
        constraint=validate_url_parameters,
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

    categories_mappings = schema.List(
        title=_(u"Categories mappings"),
        value_type=DictRow(title=u"Category mapping", schema=ICategoryMappingRowSchema),
        required=False,
    )

    representatives_mappings = schema.List(
        title=_(u"Representatives mappings"),
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

    directives.widget(header_color=ColorSelectFieldWidget)
    header_color = schema.TextLine(
        title=_("Header color"),
        required=True,
        default="#ffffff",
        constraint=validate_color_parameters,
    )

    directives.widget(nav_color=ColorSelectFieldWidget)
    nav_color = schema.TextLine(
        title=_("Navigation bar color"),
        required=True,
        default="#007bb1",  # Plone blue
        constraint=validate_color_parameters,
    )

    directives.widget(nav_text_color=ColorSelectFieldWidget)
    nav_text_color = schema.TextLine(
        title=_("Navigation bar text color"),
        required=True,
        default="#ffffff",
        constraint=validate_color_parameters,
    )

    directives.widget(links_color=ColorSelectFieldWidget)
    links_color = schema.TextLine(
        title=_("Links text color"),
        required=True,
        default="#cccccc",
        constraint=validate_color_parameters,
    )

    directives.widget(footer_color=ColorSelectFieldWidget)
    footer_color = schema.TextLine(
        title=_("Footer color"),
        required=True,
        default="#2e3133",
        constraint=validate_color_parameters,
    )

    directives.widget(footer_text_color=ColorSelectFieldWidget)
    footer_text_color = schema.TextLine(
        title=_("Footer text color"),
        required=True,
        default="#cccccc",
        constraint=validate_color_parameters,
    )


@implementer(IInstitution)
class Institution(Container):
    """
    """


class AddForm(add.DefaultAddForm):
    portal_type = "Institution"

    def updateFields(self):
        super(AddForm, self).updateFields()
        self.fields["categories_mappings"].widgetFactory = DataGridFieldFactory
        self.fields["representatives_mappings"].widgetFactory = DataGridFieldFactory

    def updateWidgets(self):
        super(AddForm, self).updateWidgets()
        self.widgets["categories_mappings"].allow_reorder = True
        self.widgets["categories_mappings"].allow_reorder = True


class AddView(add.DefaultAddView):
    form = AddForm


class EditForm(edit.DefaultEditForm):
    portal_type = "Institution"

    def updateFields(self):
        super(EditForm, self).updateFields()
        self.fields["categories_mappings"].widgetFactory = DataGridFieldFactory
        self.fields["representatives_mappings"].widgetFactory = DataGridFieldFactory

    def updateWidgets(self):
        super(EditForm, self).updateWidgets()
        self.widgets["categories_mappings"].allow_reorder = True
        self.widgets["representatives_mappings"].allow_reorder = True
