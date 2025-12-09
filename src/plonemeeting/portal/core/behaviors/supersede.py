from plone.app.z3cform.widgets.contentbrowser import ContentBrowserFieldWidget
from plone.autoform.directives import widget
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from plonemeeting.portal.core.utils import get_linked_items_chain
from z3c.relationfield import RelationChoice
from zope.interface import provider, implementer

from plonemeeting.portal.core import _

from zope.interface import Invalid


def validate_no_already_superseded(value):
    """Validator to prevent superseding a publication already superseded."""
    adapter = SupersedeAdapter(value)
    if adapter.has_superseded_by_items():
        raise Invalid(
            _(
                "error_already_superseded",
                default="This item is already superseded by another item and thus cannot be superseded again. "
                        "Please choose another, non-superseded item."
            )
        )
    return True


@provider(IFormFieldProvider)
class ISupersede(model.Schema):
    model.fieldset(
        "categorization",
        fields=["supersede"],
    )
    widget(
        "supersede",
        ContentBrowserFieldWidget,
        vocabulary="plone.app.vocabularies.Catalog",
        pattern_options={
            "recentlyUsed": True,
            "browseableTypes": ["Folder"],
            "selectableTypes": ["Publication"],
            "attribute": ['UID', 'Title', 'portal_type', 'path', "effective"],
        },
    )
    supersede = RelationChoice(
        title=_("Supersede"),
        description=_("Supersede this item."),
        default=[],
        vocabulary="plone.app.vocabularies.Catalog",
        required=False,
        constraint=validate_no_already_superseded,
    )


@implementer(ISupersede)
class SupersedeAdapter:
    def __init__(self, context):
        self.context = context

    def superseded_by_items(self):
        """Return items that superseded (replaced) this one - newer versions."""
        return get_linked_items_chain(self.context, "supersede", reverse=True, unrestricted=True)

    def supersedes_items(self):
        """Return items that this one supersedes (replaces) - older versions."""
        return get_linked_items_chain(self.context, "supersede", reverse=False, unrestricted=True)

    def has_superseded_by_items(self):
        """Check if this item has been superseded by newer items."""
        return bool(self.superseded_by_items())

    def has_supersedes_items(self):
        """Check if this item supersedes older items."""
        return bool(self.supersedes_items())
