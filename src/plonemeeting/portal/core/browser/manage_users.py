from plone import api
from plone.app.users.schema import checkEmailAddress
from plone.app.users.schema import ProtectedEmail
from plone.app.users.schema import ProtectedTextLine
from plone.autoform import directives
from plone.autoform.form import AutoExtensibleForm
from plone.base import PloneMessageFactory as _plone
from plone.protect.interfaces import IDisableCSRFProtection
from plone.protect.utils import addTokenToUrl
from plone.z3cform.layout import wrap_form
from plonemeeting.portal.core import _
from plonemeeting.portal.core import logger
from plonemeeting.portal.core.config import MANAGEABLE_INSTITUTION_SUFFIXES
from plonemeeting.portal.core.keycloak import fetch_institution_keycloak_users
from plonemeeting.portal.core.utils import get_members_group_id
from plonemeeting.portal.core.vocabularies import InstitutionManageableGroupsVocabulary
from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from z3c.form import button
from z3c.form import form
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from zope import schema
from zope.interface import alsoProvides
from zope.interface import Interface


# Values of the ``account_type`` member property: SSO for Keycloak-provisioned
# accounts (set by the sync), local for accounts managed inside Plone.
SSO_ACCOUNT_TYPE = "sso"
LOCAL_ACCOUNT_TYPE = "local"


def get_user_manageable_institution_groups(username):
    """Return institution-related group ids a Plone user currently belongs to."""
    return [
        group.getId()
        for group in api.group.get_groups(username=username)
        if any(suffix in group.getId() for suffix in MANAGEABLE_INSTITUTION_SUFFIXES)
    ]


def unregister_user_from_institution(institution, username, group_tool=None):
    """Remove ``username`` from the institution's members and manageable groups.

    The Plone user account is left intact so historical authorship is preserved.
    """
    if group_tool is None:
        group_tool = getToolByName(institution, "portal_groups")
    for group_id in get_user_manageable_institution_groups(username):
        group_tool.removePrincipalFromGroup(username, group_id)
    group_tool.removePrincipalFromGroup(username, get_members_group_id(institution))


# ================================ Local Users =================================

class ManageUsersListingView(BrowserView):
    """Unified listing of the institution's users (local and SSO).

    For SSO institutions (``authentication == 'oidc'``) the members are
    reconciled with Keycloak on every load; a sync failure is surfaced as
    an error (``sso_sync_failed``) rather than shown as a stale or
    misclassified list.
    """

    label = _("label_manage_users")
    description = _("desc_manage_users")

    def __call__(self):
        self.is_sso_institution = getattr(self.context, "authentication", "plone") == "oidc"
        self.sso_sync_failed = False
        if self.is_sso_institution:
            # The sync performs ZODB writes (creating users, group
            # membership) on a GET request; opt out of plone.protect's
            # auto-CSRF check.
            alsoProvides(self.request, IDisableCSRFProtection)
            self.sso_sync_failed = sync_institution_keycloak_users(self.context) is None
        self.users = self.context.get_all_institution_users()
        self.unregister_url = addTokenToUrl(f"{self.context.absolute_url()}/@@manage-edit-user?unregister=1")
        return self.index()

    def is_sso_user(self, user):
        """Whether ``user`` is an SSO-provisioned (Keycloak) account."""
        return user.getProperty("account_type", "") == SSO_ACCOUNT_TYPE

    def sso_management_url(self):
        """External URL (myiMio) where SSO users are added, from the registry."""
        return api.portal.get_registry_record(
            "plonemeeting.portal.core.sso_management_url", default=""
        )


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
        user_manageable_groups = []
        for group in all_user_groups:
            group_id = group.getId()
            # Keep only groups that are institution-related
            if any(suffix in group_id for suffix in MANAGEABLE_INSTITUTION_SUFFIXES):
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
        """Remove the user from the institution's members + manageable groups."""
        unregister_user_from_institution(self.context, username, group_tool=self.group_tool)

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


# ================================= Keycloak SSO =================================


def sync_institution_keycloak_users(institution):
    """Reconcile Plone members of ``institution`` with the institution's
    Keycloak realm membership (filtered by the configured group).

    Returns a ``(created, updated, removed)`` counters tuple. Returns
    ``None`` and logs a warning when Keycloak is not reachable or not
    configured for this institution — callers should surface that as a
    sync failure rather than a silent empty reconciliation.
    """
    keycloak_users = fetch_institution_keycloak_users(institution)
    if keycloak_users is None:
        return None

    acl_users = getToolByName(institution, "acl_users")
    registration = getToolByName(institution, "portal_registration")
    portal_membership = getToolByName(institution, "portal_membership")
    group_tool = getToolByName(institution, "portal_groups")
    members_group_id = get_members_group_id(institution)

    created = 0
    updated = 0
    keycloak_user_ids = set()
    for kc_user in keycloak_users:
        email = (kc_user.get("email") or "").strip()
        if not email:
            continue
        if kc_user.get("enabled") is False:
            continue

        userid = email
        keycloak_user_ids.add(userid)
        fullname = "{0} {1}".format(
            kc_user.get("firstName") or "", kc_user.get("lastName") or ""
        ).strip()
        properties = {"email": email, "username": userid, "fullname": fullname}

        existing_user = acl_users.getUserById(userid)
        if existing_user is None:
            password = registration.generatePassword()
            registration.addMember(userid, password, ["Member"], properties=properties)
            created += 1
        else:
            member = portal_membership.getMemberById(userid)
            if member is not None:
                current = {
                    "email": member.getProperty("email", ""),
                    "fullname": member.getProperty("fullname", ""),
                }
                if current["email"] != email or current["fullname"] != fullname:
                    member.setMemberProperties(mapping={"email": email, "fullname": fullname})
                    updated += 1

        # Flag the account as SSO-managed (idempotent; also backfills users
        # provisioned before this marker existed).
        member = portal_membership.getMemberById(userid)
        if member is not None and member.getProperty("account_type", "") != SSO_ACCOUNT_TYPE:
            member.setMemberProperties(mapping={"account_type": SSO_ACCOUNT_TYPE})

        group_tool.addPrincipalToGroup(userid, members_group_id)

    removed = 0
    members_group = group_tool.getGroupById(members_group_id)
    if members_group is not None:
        # Only reconcile SSO-managed accounts: a member flagged as SSO that is
        # no longer enabled/present in Keycloak loses access (its Plone account
        # is kept for authorship history). Local accounts are never touched.
        for member in list(members_group.getGroupMembers()):
            userid = member.id
            if userid in keycloak_user_ids:
                continue
            if member.getProperty("account_type", "") != SSO_ACCOUNT_TYPE:
                continue
            unregister_user_from_institution(
                institution, userid, group_tool=group_tool
            )
            removed += 1

    logger.info(
        "Keycloak SSO sync for {0}: created={1} updated={2} removed={3}".format(
            institution.getId(), created, updated, removed
        )
    )
    return (created, updated, removed)


_SSO_MANAGED_FIELD = _(
    "help_sso_managed_field",
    default="This field is managed by your identity provider (SSO) and cannot be changed here.",
)


class IManageSSOUserForm(Interface):

    username = schema.ASCIILine(
        title=_plone("label_user_name", default="User Name"),
        description=_SSO_MANAGED_FIELD,
        required=False,
    )

    email = ProtectedEmail(
        title=_("label_email", default="Email"),
        description=_SSO_MANAGED_FIELD,
        required=True,
        constraint=checkEmailAddress,
    )

    fullname = ProtectedTextLine(
        title=_("label_fullname", default="Full Name"),
        description=_SSO_MANAGED_FIELD,
        required=False,
    )

    directives.widget("user_groups", CheckBoxFieldWidget, multiple="multiple")
    user_groups = schema.List(
        title="label_groups",
        description=_("help_select_groups"),
        value_type=schema.Choice(vocabulary="plonemeeting.portal.institution_manageable_groups_vocabulary"),
        required=False,
    )


class ManageEditSSOUserForm(BaseManageUserForm):
    schema = IManageSSOUserForm
    ignoreContext = True
    label = _("label_manage_edit_user")
    description = _(
        "desc_manage_edit_sso_user",
        default="The username, email address and full name of this user are managed by your "
        "identity provider (SSO) and cannot be changed here. You can only manage this user's "
        "roles within your institution.",
    )

    def updateWidgets(self, prefix=None):
        super().updateWidgets(prefix)
        username = self.request.form.get(
            "username", self.request.form.get("form.widgets.username", None)
        )
        if not username:
            return

        user_obj = self.acl_users.getUserById(username)
        if not user_obj:
            return

        member = self.portal_membership.getMemberById(username)
        if not member:
            return

        # Keycloak owns identity fields; the form only manages permissions.
        self.widgets["username"].value = username
        self.widgets["username"].readonly = "readonly"
        self.widgets["email"].value = member.getProperty("email", "")
        self.widgets["email"].readonly = "readonly"
        self.widgets["fullname"].value = member.getProperty("fullname", "")
        self.widgets["fullname"].readonly = "readonly"
        self.widgets["user_groups"].value = self.get_manageable_groups_for_user(username)

    @button.buttonAndHandler(_plone("save"), name="save")
    def handleSave(self, action):
        """Update the SSO user's group membership (Keycloak owns the rest)."""
        data, errors = self.extractData()
        username = (data.get("username") or "").strip()
        groups_to_assign = data.get("user_groups", [])
        existing_user = username and self.acl_users.getUserById(username)
        member = username and self.portal_membership.getMemberById(username)
        if not existing_user or not member:
            self.messages.add(_("msg_user_error"), type="error")
            self.request.response.redirect("manage-users-listing")
            return
        self.update_user_groups(username, groups_to_assign)
        self.messages.add(_("msg_user_updated"), type="info")
        self.request.response.redirect("manage-users-listing")


ManageEditSSOUserFormView = wrap_form(ManageEditSSOUserForm)


# ========================= Local -> SSO account migration =====================


def _reassign_content_ownership(catalog, institution_path, old_id, new_user):
    """Reassign every object under ``institution_path`` created by ``old_id``
    to ``new_user`` (Zope owner + Owner local role + Creator), and reindex.
    Returns the number of objects reassigned."""
    new_id = new_user.getId()
    count = 0
    for brain in catalog.unrestrictedSearchResults(path=institution_path, Creator=old_id):
        obj = brain.getObject()
        obj.changeOwnership(new_user, recursive=False)
        roles = obj.get_local_roles_for_userid(old_id)
        if roles:
            obj.manage_delLocalRoles([old_id])
            obj.manage_addLocalRoles(new_id, list(roles))
        obj.creators = tuple(new_id if creator == old_id else creator for creator in (obj.creators or ()))
        obj.reindexObject(idxs=["Creator", "listCreators"])
        obj.reindexObjectSecurity()
        count += 1
    return count


def migrate_institution_local_users(institution):
    """Migrate the institution's local accounts to their SSO identity.

    For each local member whose email matches an existing SSO account (whose
    userid is that email): copy its group memberships to the SSO account,
    reassign the content it owns in the institution, then delete the local
    account. Returns a summary dict with ``migrated`` (list of (old, new)),
    ``skipped`` (list of old ids without a matching SSO account) and
    ``content`` (number of reassigned objects).
    """
    catalog = getToolByName(institution, "portal_catalog")
    group_tool = getToolByName(institution, "portal_groups")
    institution_path = "/".join(institution.getPhysicalPath())
    summary = {"migrated": [], "skipped": [], "content": 0}
    for member in institution.get_all_institution_users():
        old_id = member.getId()
        if member.getProperty("account_type", "") == SSO_ACCOUNT_TYPE:
            continue
        email = (member.getProperty("email", "") or "").strip()
        new_member = api.user.get(userid=email) if email else None
        if not email or email == old_id or new_member is None:
            summary["skipped"].append(old_id)
            continue
        for group in api.group.get_groups(username=old_id):
            if group.getId() != "AuthenticatedUsers":
                group_tool.addPrincipalToGroup(email, group.getId())
        summary["content"] += _reassign_content_ownership(
            catalog, institution_path, old_id, new_member.getUser()
        )
        api.user.delete(username=old_id)
        summary["migrated"].append((old_id, email))
    return summary


class MigrateInstitutionUsersView(BrowserView):
    """Admin-only (cmf.ManagePortal): migrate an institution's local accounts
    to their SSO identity, after a confirmation page."""

    label = _("label_migrate_users")

    def local_users(self):
        """Local members with their SSO target and owned-content count."""
        catalog = getToolByName(self.context, "portal_catalog")
        institution_path = "/".join(self.context.getPhysicalPath())
        rows = []
        for member in self.context.get_all_institution_users():
            old_id = member.getId()
            if member.getProperty("account_type", "") == SSO_ACCOUNT_TYPE:
                continue
            email = (member.getProperty("email", "") or "").strip()
            rows.append(
                {
                    "id": old_id,
                    "email": email,
                    "ready": bool(email) and email != old_id and api.user.get(userid=email) is not None,
                    "content_count": len(
                        catalog.unrestrictedSearchResults(path=institution_path, Creator=old_id)
                    ),
                }
            )
        return rows

    def __call__(self):
        if self.request.method == "POST":
            summary = migrate_institution_local_users(self.context)
            IStatusMessage(self.request).addStatusMessage(
                _(
                    "msg_users_migrated",
                    default="Migrated ${migrated} account(s), reassigned ${content} "
                    "content item(s), skipped ${skipped}.",
                    mapping={
                        "migrated": len(summary["migrated"]),
                        "content": summary["content"],
                        "skipped": len(summary["skipped"]),
                    },
                ),
                type="info",
            )
            self.request.response.redirect(f"{self.context.absolute_url()}/@@manage-users-listing")
            return ""
        return self.index()
