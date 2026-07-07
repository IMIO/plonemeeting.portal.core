# -*- coding: utf-8 -*-
from plone import api
from plonemeeting.portal.core import _
from plonemeeting.portal.core.content.institution import IInstitution
from Products.CMFPlone.browser.exceptions import ExceptionView
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile


def _is_content(obj):
    """True for a real (traversable) content object, False for an exception
    instance or anything without a physical path."""
    return obj is not None and not isinstance(obj, Exception) and hasattr(obj, "getPhysicalPath")


class _NotFoundMixin:
    """Shared logic for the themed 404 page: resolve the relevant context
    and build the "back" target (the Institution the user was inside, or the
    portal homepage). Used both as the NotFound exception view and rendered
    programmatically (see ``events.exceptions``)."""

    def _best_context(self):
        """Return the most relevant content object. As an exception view,
        ``self.context`` is the exception and ``self.__parent__`` is the
        object that was being published; fall back to the portal."""
        ctx = getattr(self, "context", None)
        if not _is_content(ctx):
            ctx = getattr(self, "__parent__", None)
        if not _is_content(ctx):
            ctx = api.portal.get()
        return ctx

    def get_institution(self):
        """The Institution (navigation root) the failed request was inside,
        or None when at the portal root / undeterminable (-> homepage)."""
        ctx = self._best_context()
        nav_root = api.portal.get_navigation_root(ctx)
        if IInstitution.providedBy(nav_root):
            return nav_root
        # The publish may have failed before reaching the institution, leaving
        # the portal as best context: recover the institution from the URL.
        return self._institution_from_request()

    def _institution_from_request(self):
        portal = api.portal.get()
        url = self.request.get("ACTUAL_URL", "") or ""
        portal_url = portal.absolute_url()
        if url.startswith(portal_url):
            rest = url[len(portal_url):]
        else:
            rest = self.request.get("PATH_INFO", "") or ""
        segments = [s for s in rest.split("/") if s]
        first = segments[0] if segments else None
        if first and first in portal:
            candidate = portal[first]
            if IInstitution.providedBy(candidate):
                return candidate
        return None

    def is_in_institution(self):
        return self.get_institution() is not None

    def back_url(self):
        institution = self.get_institution()
        if institution is not None:
            return institution.absolute_url()
        return api.portal.get().absolute_url()

    def back_label(self):
        institution = self.get_institution()
        if institution is not None:
            return _(
                "notfound_back_to_institution",
                default="Retour à l'accueil de ${title}",
                mapping={"title": institution.Title()},
            )
        return _("notfound_back_to_home", default="Retour à l'accueil")


class NotFoundExceptionView(ExceptionView, _NotFoundMixin):
    """Themed 404 page wired as the ``NotFound`` exception view. Inherits the
    status/JSON/redirect handling of CMFPlone's ExceptionView and only swaps
    the template."""

    index = ViewPageTemplateFile("templates/notfound.pt")


class NotFoundView(BrowserView, _NotFoundMixin):
    """Standalone ``@@notfound`` view, for programmatic rendering and tests."""

    index = ViewPageTemplateFile("templates/notfound.pt")

    def __call__(self):
        self.request.response.setStatus(404)
        self.request.set("disable_border", True)
        self.request.set("disable_plone.leftcolumn", True)
        self.request.set("disable_plone.rightcolumn", True)
        return self.index()
