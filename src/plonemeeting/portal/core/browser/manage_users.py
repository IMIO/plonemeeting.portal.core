from collective.z3cform.datagridfield.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield.row import DictRow
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
from plonemeeting.portal.core.config import SSO_ACCOUNT_TYPE
from plonemeeting.portal.core.keycloak import fetch_institution_keycloak_users
from plonemeeting.portal.core.utils import get_members_group_id
from plonemeeting.portal.core.vocabularies import InstitutionManageableGroupsVocabulary
from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from urllib.parse import quote
from z3c.form import button
from z3c.form import form
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from zope import schema
from zope.interface import alsoProvides
from zope.interface import Interface

import os
import transaction


def get_user_manageable_institution_groups(username, institution):
    """Return the manageable group ids of ``institution`` that ``username`` is in.

    Institution groups are named ``{institution_id}-{suffix}``. Matching on the
    suffix alone would also return the groups of every *other* institution, so
    unregistering a user here would revoke their access everywhere.
    """
    prefix = "{0}-".format(institution.getId())
    manageable = {
        "{0}{1}".format(prefix, suffix) for suffix in MANAGEABLE_INSTITUTION_SUFFIXES
    }
    return [
        group.getId()
        for group in api.group.get_groups(username=username)
        if group.getId() in manageable
    ]


def unregister_user_from_institution(institution, username, group_tool=None):
    """Remove ``username`` from the institution's members and manageable groups.

    The Plone user account is left intact so historical authorship is preserved.
    """
    if group_tool is None:
        group_tool = getToolByName(institution, "portal_groups")
    for group_id in get_user_manageable_institution_groups(username, institution):
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

    def _quoted_user_id(self, user):
        """Query-string-safe user id.

        SSO user ids are email addresses, so they may contain characters
        (``+``, ``&``, ``#``) that would otherwise be mangled or truncated when
        the URL is parsed back into a form value. ``@`` is left as-is: it is
        legal unencoded in a query string and keeps the URLs readable.
        """
        return quote(user.getId(), safe="@")

    def edit_url(self, user):
        """Type-specific edit URL with a safely encoded username."""
        view_name = "@@manage-edit-sso-user" if self.is_sso_user(user) else "@@manage-edit-user"
        return "{0}?username={1}".format(view_name, self._quoted_user_id(user))

    def unregister_user_url(self, user):
        """CSRF-tokened unregister URL with a safely encoded username."""
        return "{0}&username={1}".format(self.unregister_url, self._quoted_user_id(user))

    def keycloak_add_user_url(self):
        """External URL where institution managers add SSO users."""
        return os.environ.get("keycloak_add_user_url", "")


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
        """The manageable groups of *this* institution that ``username`` is in.

        Scoped to ``self.context``: the widget vocabulary only offers this
        institution's groups, so returning another one's would be a value the
        checkbox widget cannot render.
        """
        return get_user_manageable_institution_groups(username, self.context)

    def is_institution_member(self, username):
        """Whether ``username`` already belongs to this institution.

        The edit forms post the username back in a readonly widget, so it is
        client-controlled: without this check a manager could point the form at
        any portal account and attach it to this institution's groups. Joining
        a new account is what ``InviteUserForm`` is for.
        """
        group = self.group_tool.getGroupById(get_members_group_id(self.context))
        return group is not None and username in group.getGroupMemberIds()

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
        if errors:
            self.messages.add(self.formErrorsMessage, type="error")
            return
        username = data["username"].strip()
        email = data.get("email", "").strip()
        fullname = data.get("fullname", "").strip()
        groups_to_assign = data.get("user_groups", [])
        existing_user = self.acl_users.getUserById(username)
        if existing_user:
            # The username is posted back by a readonly widget, so editing is
            # restricted to accounts this institution already has.
            if not self.is_institution_member(username):
                self.messages.add(_("msg_user_error"), type="error")
                self.request.response.redirect("manage-users-listing")
                return
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
            except Exception:
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
        if errors:
            self.messages.add(self.formErrorsMessage, type="error")
            return
        username = (data.get("username") or "").strip()
        groups_to_assign = data.get("user_groups", [])
        existing_user = username and self.acl_users.getUserById(username)
        member = username and self.portal_membership.getMemberById(username)
        if not existing_user or not member or not self.is_institution_member(username):
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


def migrate_institution_user(institution, old_id, new_id, catalog=None, group_tool=None):
    """Migrate account ``old_id`` onto ``new_id`` within ``institution``.

    Copy the source account's group memberships to the target, reassign the
    content the source owns in the institution, then delete the source account
    -- unless it still owns content in another institution, in which case it is
    kept and gets deleted when that institution is migrated in turn.
    Returns the number of content items reassigned.
    """
    if catalog is None:
        catalog = getToolByName(institution, "portal_catalog")
    if group_tool is None:
        group_tool = getToolByName(institution, "portal_groups")
    for group in api.group.get_groups(username=old_id):
        if group.getId() != "AuthenticatedUsers":
            group_tool.addPrincipalToGroup(new_id, group.getId())
    institution_path = "/".join(institution.getPhysicalPath())
    count = _reassign_content_ownership(
        catalog, institution_path, old_id, api.user.get(userid=new_id).getUser()
    )
    # Content still owned lives in another institution; deleting the account
    # would orphan its Creator. Keep it (it converges when that institution is
    # migrated) but strip it from this institution's groups.
    remaining = len(catalog.unrestrictedSearchResults(Creator=old_id))
    if remaining:
        unregister_user_from_institution(institution, old_id, group_tool=group_tool)
        logger.info(
            "Kept user %s: %d content item(s) left in other institution(s)",
            old_id, remaining,
        )
    else:
        # delete_localroles=0: the default runs a site-wide security reindex
        # (minutes/account) that _reassign_content_ownership already made moot.
        getToolByName(institution, "portal_membership").deleteMembers(
            (old_id,), delete_localroles=0
        )
    logger.info("Migrated user %s -> %s: %d content item(s)", old_id, new_id, count)
    return count


def migrate_institution_local_users(institution):
    """Migrate the institution's local accounts to their SSO identity.

    For each local member whose email matches an existing SSO account (whose
    userid is that email): copy its group memberships to the SSO account,
    reassign the content it owns in the institution, then delete the local
    account. Returns a summary dict with ``migrated`` (list of (old, new)),
    ``skipped`` (list of old ids without a matching SSO account), ``failed``
    (list of old ids whose migration raised) and ``content`` (number of
    reassigned objects).

    The institution's Keycloak accounts are synced first, so freshly
    provisioned SSO identities are matchable; when that sync fails nothing
    is migrated and ``None`` is returned.
    """
    institution_id = institution.getId()
    if sync_institution_keycloak_users(institution) is None:
        logger.warning("User migration for %s: Keycloak sync failed", institution_id)
        return None
    catalog = getToolByName(institution, "portal_catalog")
    group_tool = getToolByName(institution, "portal_groups")
    summary = {"migrated": [], "skipped": [], "failed": [], "content": 0}
    for member in institution.get_all_institution_users():
        old_id = member.getId()
        if member.getProperty("account_type", "") == SSO_ACCOUNT_TYPE:
            continue
        email = (member.getProperty("email", "") or "").strip()
        if not email:
            reason = "no email address"
        elif email == old_id:
            reason = "userid is already an email address"
        elif api.user.get(userid=email) is None:
            reason = "no SSO account for {0}".format(email)
        else:
            reason = None
        if reason:
            logger.info(
                "User migration for %s: skipping %s (%s)", institution_id, old_id, reason
            )
            summary["skipped"].append(old_id)
            continue
        # One failing account must not void the whole institution's run.
        savepoint = transaction.savepoint(optimistic=True)
        try:
            summary["content"] += migrate_institution_user(
                institution, old_id, email, catalog=catalog, group_tool=group_tool
            )
        except Exception:
            savepoint.rollback()
            logger.exception(
                "User migration for %s: %s -> %s failed", institution_id, old_id, email
            )
            summary["failed"].append(old_id)
            continue
        summary["migrated"].append((old_id, email))
    logger.info(
        "User migration for %s: migrated=%d skipped=%d failed=%d content=%d",
        institution_id,
        len(summary["migrated"]),
        len(summary["skipped"]),
        len(summary["failed"]),
        summary["content"],
    )
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
            if summary is None:
                IStatusMessage(self.request).addStatusMessage(
                    _(
                        "msg_migration_sync_failed",
                        default="The SSO server could not be reached; nothing was migrated.",
                    ),
                    type="error",
                )
            else:
                IStatusMessage(self.request).addStatusMessage(
                    _(
                        "msg_users_migrated",
                        default="Migrated ${migrated} account(s), reassigned ${content} "
                        "content item(s), skipped ${skipped}, failed ${failed}.",
                        mapping={
                            "migrated": len(summary["migrated"]),
                            "content": summary["content"],
                            "skipped": len(summary["skipped"]),
                            "failed": len(summary["failed"]),
                        },
                    ),
                    type="info",
                )
            self.request.response.redirect(f"{self.context.absolute_url()}/@@manage-users-listing")
            return ""
        return self.index()


# ==================== Manual user-to-user account migration ===================


class IUserMigrationRowSchema(Interface):
    """One source -> target account pairing in the migration grid."""

    source = schema.Choice(
        title=_("label_migration_source", default="Account to migrate"),
        vocabulary="plonemeeting.portal.vocabularies.institution_local_users",
        required=True,
    )
    target = schema.Choice(
        title=_("label_migration_target", default="Target account"),
        vocabulary="plonemeeting.portal.vocabularies.institution_sso_users",
        required=True,
    )


class IMigrateUserToUserForm(Interface):

    directives.widget(
        "migrations",
        DataGridFieldFactory,
        auto_append=True,
        display_table_css_class="table table-bordered table-striped",
    )
    migrations = schema.List(
        title=_("label_user_migrations", default="Account migrations"),
        description=_(
            "desc_user_migrations",
            default="Each source account's group memberships and content are moved to "
            "the target account, then the source account is deleted. This cannot be undone.",
        ),
        value_type=DictRow(title="Account migration", schema=IUserMigrationRowSchema),
        required=True,
    )


class MigrateUserToUserForm(BaseManageUserForm):
    """Admin-only (cmf.ManagePortal): manually migrate local accounts onto another
    account when their email does not match their SSO identity, so the automatic
    email-based migration cannot pair them (e.g. jdupont@ -> jean.dupont@)."""

    schema = IMigrateUserToUserForm
    ignoreContext = True
    label = _("label_migrate_user_to_user", default="Migrate a user to another user")
    description = _(
        "desc_migrate_user_to_user",
        default="Migrate a local account onto another account, for accounts whose email "
        "address does not match their SSO identity.",
    )

    @button.buttonAndHandler(_("label_confirm_migration"), name="migrate")
    def handleMigrate(self, action):
        data, errors = self.extractData()
        if errors:
            self.messages.add(self.formErrorsMessage, type="error")
            return
        migrated = 0
        content = 0
        for row in data.get("migrations") or []:
            source = row.get("source")
            target = row.get("target")
            # The vocabularies already restrict the choices, but the grid is
            # client-controlled: only migrate a source that is a member of this
            # institution onto a distinct, existing target account.
            if not source or not target or source == target:
                continue
            if not self.is_institution_member(source) or api.user.get(userid=target) is None:
                continue
            content += migrate_institution_user(
                self.context, source, target, group_tool=self.group_tool
            )
            migrated += 1
        self.messages.add(
            _(
                "msg_users_migrated_manual",
                default="Migrated ${migrated} account(s), reassigned ${content} content item(s).",
                mapping={"migrated": migrated, "content": content},
            ),
            type="info",
        )
        self.request.response.redirect(f"{self.context.absolute_url()}/@@manage-users-listing")


MigrateUserToUserFormView = wrap_form(MigrateUserToUserForm)
