# -*- coding: utf-8 -*-

from collective.z3cform.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield import DictRow
from plone.app.textfield import RichText
from plone.dexterity.browser import add
from plone.dexterity.browser import edit
from plone.dexterity.content import Container
from plone.supermodel import model
from zope import schema
from zope.interface import Interface
from zope.interface import implementer

from plonemeeting.portal.core import _


class ICategoryMappingRowSchema(Interface):
    global_category = schema.TextLine(title=_(u"Global category"))
    local_category = schema.TextLine(title=_(u"Local category"))


class IRepresentativeMappingRowSchema(Interface):
    representative_key = schema.TextLine(title=_(u"Reprensentative key"))
    representative_value = schema.TextLine(title=_(u"Reprensentative value"))
    representative_long_value = schema.TextLine(title=_(u"Reprensentative long values"))
    representative_group_in_charge_key = schema.TextLine(
        title=_(u"Reprensentative group in charge key")
    )
    active = schema.Bool(title=_(u"Active"))


class IInstitution(model.Schema):
    """ Marker interface and Dexterity Python Schema for Institution
    """

    url = schema.URI(title=_(u"Plonemeeting URL"), required=False)

    username = schema.TextLine(title=_(u"Username"), required=False)

    password = schema.Password(title=_(u"Password"), required=False)

    meeting_config_id = schema.TextLine(title=_(u"Meeting config ID"), required=False)

    info_points_formatting_tal = schema.TextLine(
        title=_(u"Info points formatting tal expression"), required=False
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

    text = RichText(title=_(u"Text"), required=False)


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


class AddView(add.DefaultAddView):
    form = AddForm


class EditForm(edit.DefaultEditForm):
    portal_type = "Institution"

    def updateFields(self):
        super(EditForm, self).updateFields()
        self.fields["categories_mappings"].widgetFactory = DataGridFieldFactory
        self.fields["representatives_mappings"].widgetFactory = DataGridFieldFactory
