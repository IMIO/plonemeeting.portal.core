# -*- coding: utf-8 -*-
from DateTime import DateTime
from zope.container.contained import ContainerModifiedEvent


def publication_modified(obj, event):
    """Reindex "has_annexes" when adding/removing an annex."""
    # reindex if element in container modified (annex)
    if isinstance(event, ContainerModifiedEvent):
        obj.reindexObject(idxs=["has_annexes"], update_metadata=False)


def publication_state_changed(publication, event):
    """Set effective_date if empty when "publish"."""
    # bypass if creating institution
    if event.transition is None:
        return

    if event.new_state.id == 'published' and publication.effective_date is None:
        publication.setEffectiveDate(DateTime())
