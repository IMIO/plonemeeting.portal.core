from imio.pyutils.utils import sort_by_indexes
from plone.dexterity.browser.add import DefaultAddForm
from plone.dexterity.browser.edit import DefaultEditForm
from Products.CMFCore.utils import getToolByName


class BaseFormMixin:
    zope_admin_fieldsets = ()
    fieldsets_order = ()
    context = None

    def _sort_fieldsets(self):
        """
        Sorts the groups of fieldsets based on their
        corresponding indexes in the `fieldsets_order` attribute.
        `fieldsets_order` should contain either ALL the fieldset group names or be empty.
        """
        indexes = [self.fieldsets_order.index(group.__name__) for group in self.groups]
        self.groups = sort_by_indexes(self.groups, indexes)

    def _remove_admin_fieldsets(self):
        """
        Ensures that only users with "Manage portal" permission can access or
        manipulate specific fieldsets defined in the `zope_admin_fieldsets` attribute.
        """
        pm = getToolByName(self.context, "portal_membership")
        if not pm.checkPermission("Manage portal", self.context):
            self.groups = list(filter(lambda g: g.__name__ not in self.zope_admin_fieldsets, self.groups))


class BaseAddForm(DefaultAddForm, BaseFormMixin):

    def __init__(self, context, request):
        super().__init__(context, request)
        self.context = context
        self.utils_view = self.context.restrictedTraverse("@@utils_view")
        self.institution = self.utils_view.get_current_institution()

    def updateFields(self):
        super().updateFields()
        if self.zope_admin_fieldsets:
            self._remove_admin_fieldsets()
        if self.fieldsets_order:
            self._sort_fieldsets()


class BaseEditForm(DefaultEditForm, BaseFormMixin):

    def __init__(self, context, request):
        super().__init__(context, request)
        self.context = context
        self.utils_view = self.context.restrictedTraverse("@@utils_view")
        self.institution = self.utils_view.get_current_institution()

    def updateFields(self):
        super().updateFields()
        if self.zope_admin_fieldsets:
            self._remove_admin_fieldsets()
        if self.fieldsets_order:
            self._sort_fieldsets()
