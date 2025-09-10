from plone import api
from plone.app.users.schema import checkEmailAddress
from plone.app.users.schema import ProtectedEmail
from plone.app.users.schema import ProtectedTextLine
from plone.autoform import directives
from plone.autoform.form import AutoExtensibleForm
from plone.base import PloneMessageFactory as _plone
from plone.protect.utils import addTokenToUrl
from plone.z3cform.layout import wrap_form
from plonemeeting.portal.core import _
from plonemeeting.portal.core.utils import get_members_group_id
# from plonemeeting.portal.core.utils import get_manageable_groups_for_user
from plonemeeting.portal.core.vocabularies import InstitutionManageableGroupsVocabulary
from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from z3c.form import button
from z3c.form import form
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from zope import schema
from zope.interface import Interface


class ManageUsersListingView(BrowserView):
    """
    Shows a manageable listing of the institution's users.
    """

    label = _("label_manage_users")
    description = _("desc_manage_users")

    def __call__(self):
        self.users = self.context.get_all_institution_users()
        self.unregister_url = addTokenToUrl(f"{self.context.absolute_url()}/@@manage-edit-user?unregister=1")
        return self.index()


class IManageUserForm(Interface):
    """Schema for user management form, focusing on groups now."""

    username = schema.ASCIILine(
        title=_plone("label_user_name", default="User Name"),
        description=_(
            "help_user_name_creation_casesensitive",
            default="Enter a user name, usually something like 'jsmith'. "
            "No spaces or special characters. Usernames and "
            "passwords are case sensitive, make sure the caps lock "
            "key is not enabled. This is the name used to log in.",
        ),
    )
    email = ProtectedEmail(
        title=_("label_email", default="Email"),
        description=_("We will use this address if you need to recover your password"),
        required=True,
        constraint=checkEmailAddress,
    )
    fullname = ProtectedTextLine(
        title=_("label_fullname", default="Full Name"),
        description=_("help_full_name_creation", default="Enter full name, e.g. John Smith."),
        required=False,
    )
    directives.widget("user_groups", CheckBoxFieldWidget, multiple="multiple")
    user_groups = schema.List(
        title="label_groups",
        description=_("help_select_groups"),
        value_type=schema.Choice(vocabulary="plonemeeting.portal.institution_manageable_groups_vocabulary"),
        required=False,
    )


class IInviteUserForm(Interface):
    """Schema for inviting a user to a group."""

    username = schema.ASCIILine(
        title=_plone("label_user_name", default="User Name"),
        description=_(
            "help_user_name_creation_casesensitive",
            default="Enter a user name, usually something like 'jsmith'. "
            "No spaces or special characters. Usernames and "
            "passwords are case sensitive, make sure the caps lock "
            "key is not enabled. This is the name used to log in.",
        ),
    )


class BaseManageUserForm(AutoExtensibleForm, form.Form):
    schema = IManageUserForm

    def update(self):
        # Initialize tools & references
        self.acl_users = getToolByName(self.context, "acl_users")
        self.portal_membership = getToolByName(self.context, "portal_membership")
        self.registration = getToolByName(self.context, "portal_registration")
        self.group_tool = getToolByName(self.context, "portal_groups")
        self.messages = IStatusMessage(self.request)

        # Proceed with normal form setup
        super().update()

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
                user_manageable_groups.append(group_id)
        return user_manageable_groups

    def update_user_groups(self, username, selected_groups):
        vocabulary = InstitutionManageableGroupsVocabulary(self.context)
        manageable_group_ids = [t.value for t in vocabulary]
        for group_id in manageable_group_ids:
            if group_id in selected_groups:
                self.group_tool.addPrincipalToGroup(username, group_id)
            else:
                self.group_tool.removePrincipalFromGroup(username, group_id)

    def join_institution(self, username):
        """Add the user to the group."""
        self.group_tool.addPrincipalToGroup(username, get_members_group_id(self.context))

    def unregister_from_institution(self, username):
        """Remove the user from the group."""
        for groups_id in self.get_manageable_groups_for_user(username):
            self.group_tool.removePrincipalFromGroup(username, groups_id)
        self.group_tool.removePrincipalFromGroup(username, get_members_group_id(self.context))

    @button.buttonAndHandler("label_cancel_button", name="cancel")
    def handleCancel(self, action):
        """Cancel editing/creating and return to listing."""
        self.request.response.redirect("manage-users-listing")


class ManageCreateUserForm(BaseManageUserForm):
    schema = IManageUserForm
    ignoreContext = True
    label = _("label_manage_create_user")
    description = _("desc_manage_create_user")

    @button.buttonAndHandler(_plone("save"), name="save")
    def handleSave(self, action):
        """Create or update user, then update their group membership."""
        data, errors = self.extractData()
        if errors:
            IStatusMessage(self.request).addStatusMessage(self.formErrorsMessage, type="error")
            return
        username = data["username"].strip()
        email = data.get("email", "").strip()
        fullname = data.get("fullname", "").strip()
        groups_to_assign = data.get("user_groups", [])
        existing_user = self.acl_users.getUserById(username)
        if existing_user:
            IStatusMessage(self.request).addStatusMessage(_("msg_existing_user_error"), type="error")
            return
        try:
            password = self.registration.generatePassword()
            self.registration.addMember(
                username, password, ["Member"], properties={"email": email, "username": username, "fullname": fullname}
            )
            self.join_institution(username)
            self.update_user_groups(username, groups_to_assign)
            self.registration.registeredNotify(username)
            IStatusMessage(self.request).addStatusMessage(_("msg_user_created"), type="info")
        except Exception as e:
            IStatusMessage(self.request).addStatusMessage(_("msg_user_create_failed: {}").format(str(e)), type="error")
            return

        self.request.response.redirect("manage-users-listing")
        return


ManageCreateUserFormView = wrap_form(ManageCreateUserForm)


class ManageEditUsersForm(BaseManageUserForm):
    """
    Form to update an institution's user
    """

    schema = IManageUserForm
    ignoreContext = True
    label = _("label_manage_edit_user")
    description = _("desc_manage_edit_user")

    def update(self):
        super().update()

        # Check for unregister param
        unregister_flag = self.request.form.get("unregister", None)
        username = self.request.form.get("username", None)
        # If 'unregister=1' is in the query, delete immediately and redirect.
        if unregister_flag and username:
            self.unregister_from_institution(username)
            self.request.response.redirect("manage-users-listing")
            return

    def updateWidgets(self, prefix=None):
        super().updateWidgets(prefix)
        username = self.request.form.get("username", self.request.form.get("form.widgets.username", None))
        if not username:
            return

        # We have a username; let's populate the widgets if the user exists
        user_obj = self.acl_users.getUserById(username)
        if not user_obj:
            return

        member = self.portal_membership.getMemberById(username)
        if not member:
            return

        # Pre-fill user info
        self.widgets["username"].value = member.getId()
        self.widgets["username"].readonly = "readonly"  # Prevent changing username
        self.widgets["email"].value = member.getProperty("email", "")
        self.widgets["fullname"].value = member.getProperty("fullname", "")
        self.widgets["user_groups"].value = self.get_manageable_groups_for_user(username)

    @button.buttonAndHandler(_plone("save"), name="save")
    def handleSave(self, action):
        """Create or update user, then update their group membership."""
        data, errors = self.extractData()
        username = data["username"].strip()
        email = data.get("email", "").strip()
        fullname = data.get("fullname", "").strip()
        groups_to_assign = data.get("user_groups", [])
        existing_user = self.acl_users.getUserById(username)
        if existing_user:
            # Update existing user
            member = self.portal_membership.getMemberById(username)
            if member:
                member.setMemberProperties(mapping={"email": email, "fullname": fullname})
                self.update_user_groups(username, groups_to_assign)
                self.messages.add(_("msg_user_updated"), type="info")
        else:
            try:
                password = self.registration.generatePassword()
                self.registration.addMember(
                    username, password, properties={"email": email, "username": username, "fullname": fullname}
                )
                self.update_user_groups(username, groups_to_assign)
                self.registration.registeredNotify(username)
                self.messages.add(_("msg_user_created"), type="info")
            except Exception as e:
                self.messages.add(_("msg_user_create_failed"), type="error")

        self.request.response.redirect("manage-users-listing")


ManageEditUserFormView = wrap_form(ManageEditUsersForm)


class InviteUserForm(BaseManageUserForm):
    """
    z3c.form class to create/update/delete Plone users,
    with group membership (instead of roles).
    """

    schema = IInviteUserForm
    ignoreContext = True
    label = _("label_invite_user")
    description = _("desc_invite_user")

    @button.buttonAndHandler(_("label_invite_button"), name="invite")
    def handleInvite(self, action):
        """Create or update user, then update their group membership."""
        data, errors = self.extractData()
        if errors:
            IStatusMessage(self.request).addStatusMessage(self.formErrorsMessage, type="error")
            return
        username = data["username"].strip()
        existing_user = self.acl_users.getUserById(username)
        if not existing_user:
            IStatusMessage(self.request).addStatusMessage("msg_not_existing_user_error", type="error")
            return
        self.join_institution(username)


InviteUserFormView = wrap_form(InviteUserForm)
