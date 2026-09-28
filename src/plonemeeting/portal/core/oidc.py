


def sso_login_url(institution):
    """Where a migrated user should go to log in again.

    The OIDC login URL takes them straight to Wallonie Connect and back to
    their own institution. It is ``None`` when the plugin has no issuer
    configured, and the portal's login-choice page is then the honest
    fallback: that view is registered on the site root only, so it cannot be
    built from the institution.
    """
    login_url = get_login_url(came_from=institution.absolute_url())
    return login_url or f"{api.portal.get().absolute_url()}/@@login-choice"
