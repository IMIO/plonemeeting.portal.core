from AccessControl import getSecurityManager
from Acquisition import aq_inner
from Acquisition import aq_parent
from plone import api
from plonemeeting.portal.core.content.institution import IInstitution
from Products.CMFPlone.browser.exceptions import ExceptionView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zExceptions import NotFound
from zExceptions import Unauthorized


# Cookies set by the Plone session, the REST API token and the login form.
AUTH_COOKIE_NAMES = ("__ac", "auth_token", "__ginger_snap")


def has_credentials(request):
    """Return True when the request has login credentials.

    The security manager cannot tell this. It holds the anonymous user when
    the publisher refuses the access.
    """
    if request._auth:
        return True
    return any(request.cookies.get(name) for name in AUTH_COOKIE_NAMES)


class NotFoundExceptionView(ExceptionView):
    """The 404 page.

    It is the view of ``NotFound`` and of ``Unauthorized``. A visitor without
    credentials gets the same 404 response for content that is hidden and for
    content that does not exist. A user with credentials gets the usual login
    challenge.
    """

    index = ViewPageTemplateFile("templates/notfound.pt")

    def __call__(self):
        response = self.request.response
        hide = isinstance(self.context, Unauthorized) and not has_credentials(self.request)
        if hide:
            # Stop the login challenge of the user folder.
            response._has_challenged = True
            # Remove the base tag of the hidden content.
            response.setBase(None)
            self.context = NotFound()
        self.__parent__ = self._visible_parent()
        body = super().__call__()
        if hide and body is not None:
            # The publisher sets the 401 status after this call.
            response.setStatus(404, lock=1)
        return body

    def _visible_parent(self):
        """Return the nearest parent that the current user can view.

        The page must not show data from hidden content.
        """
        obj = self.__parent__
        portal = api.portal.get()
        sm = getSecurityManager()
        while obj != portal and not sm.checkPermission("View", obj):
            parent = aq_parent(aq_inner(obj))
            if parent is None:
                return portal
            obj = parent
        return obj

    def institution(self):
        """Return the institution that contains the page, or None."""
        nav_root = api.portal.get_navigation_root(self.context)
        if IInstitution.providedBy(nav_root):
            return nav_root
        return None
