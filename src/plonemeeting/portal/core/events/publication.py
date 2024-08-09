# -*- coding: utf-8 -*-
from zope.container.contained import ContainerModifiedEvent


def publication_modified(obj, event):
    """Reindex "has_annexes" when adding/removing an annex."""
    # reindex if element in container modified (annex)
    if isinstance(event, ContainerModifiedEvent):
        obj.reindexObject(idxs=["has_annexes"], update_metadata=False)
