# -*- coding: utf-8 -*-

from DateTime import DateTime
from plone import api
from plonemeeting.portal.core import _
from zExceptions import Redirect
from zope.container.contained import ContainerModifiedEvent


def publication_modified(publication, event):
    """Reindex "has_annexes" when adding/removing an annex."""
    # reindex if element in container modified (annex)
    if isinstance(event, ContainerModifiedEvent):
        publication.reindexObject(idxs=["has_annexes"], update_metadata=False)


def publication_state_changed(publication, event):
    """Set effective_date if empty when "publish"."""
    # bypass if creating institution
    if event.transition is None:
        return

    if event.new_state.id == 'published' and publication.effective_date is None:
        publication.setEffectiveDate(DateTime())
        publication.reindexObject(idxs=["effective", "effectiveRange", "year"])


def publication_will_be_removed(publication, event):
    """Raise if current user can not."""
    if not publication.is_power_user():
        api.portal.show_message(_("You must be publications power user to remove this element!"),
                                request=publication.REQUEST, type="error")
        raise Redirect(publication.REQUEST.get('HTTP_REFERER'))
