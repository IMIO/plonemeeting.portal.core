# -*- coding: utf-8 -*-
from zExceptions import Unauthorized


# Cookie names used by Plone's authentication plugins (plone.session /
# credentials_cookie_auth and the bearer-token plugin). Presence of any of
# these -- or of an Authorization header -- means the request carries
# credentials, i.e. the visitor is (trying to be) authenticated.
_AUTH_COOKIE_NAMES = ("__ac", "auth_token", "__ginger_snap")


def _is_anonymous_request(request):
    """True when the request carries no authentication credentials.

    At ``IPubBeforeAbort`` the security manager has already been reset to the
    Anonymous user for everyone, so it cannot tell apart a genuine anonymous
    visitor from a logged-in user who merely lacks access. The raw credentials
    on the request, however, are still available."""
    if getattr(request, "_auth", None):
        return False
    cookies = getattr(request, "cookies", None) or {}
    return not any(cookies.get(name) for name in _AUTH_COOKIE_NAMES)


def unauthorized_to_notfound(event):
    """DELIBE-313: turn an anonymous ``Unauthorized`` into a 404.

    By default Plone redirects an anonymous user who hits content they cannot
    view to the login form, which leaks the existence of private content.
    Instead we serve a 404, exactly as for a missing URL.

    Authenticated-but-unauthorized users are left untouched (they keep the
    normal ``insufficient-privileges`` page -- no info leak when logged in).

    The themed 404 *body* is produced upstream by the ``Unauthorized``
    exception view (``browser.exceptions.NotFoundExceptionView``, registered in
    ``browser/configure.zcml``) and themed by the transform chain. This
    ``IPubBeforeAbort`` subscriber only has to undo the login redirect that
    ``response._unauthorized()`` set just before: drop the ``Location`` header
    and force the status to 404.

    The challenge locked the status at 302 (``CookieAuthHelper`` redirects with
    ``lock=1``), so we unlock it first; we then re-lock at 404 so the
    transform chain's own ``IPubBeforeAbort`` handler cannot reset it to 401,
    whatever order the two subscribers fire in.
    """
    if not isinstance(event.exc_info[1], Unauthorized):
        return
    request = event.request
    if not _is_anonymous_request(request):
        return

    response = request.response
    response.headers.pop("location", None)
    response._locked_status = 0
    response.setStatus(404, lock=1)
