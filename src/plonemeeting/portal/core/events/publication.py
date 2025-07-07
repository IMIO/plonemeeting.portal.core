# -*- coding: utf-8 -*-
from collective.timestamp import _ as _cts
from collective.timestamp import logger as cts_logger
from collective.timestamp.behaviors.timestamp import ITimestampableDocument
from collective.timestamp.interfaces import ITimeStamper
from DateTime import DateTime
from plone import api
from plonemeeting.portal.core import _
from Products.CMFPlone.utils import parent
from zExceptions import Redirect
from zope.container.contained import ContainerModifiedEvent


def publication_modified(publication, event):
    """Reindex "has_annexes" when adding/removing an annex."""
    # reindex if element in container modified (annex)
    if isinstance(event, ContainerModifiedEvent):
        publication.reindexObject(idxs=["has_annexes"], update_metadata=False)
    if not publication.timestamp:
        return
    publication.timestamp = None
    publication.reindexObject(idxs=["is_timestamped"])
    request = getattr(publication, "REQUEST", None)
    if request is not None:
        message = _("msg_timestamp_removed")
        api.portal.show_message(message, request)



def check_publication_timestamp(obj, event):
    obj = parent(obj)
    if not ITimestampableDocument.providedBy(obj):
        return
    handler = ITimeStamper(obj)
    if not handler.file_has_changed(obj, event):
        return
    obj.timestamp = None
    obj.reindexObject(idxs=["is_timestamped"])
    request = getattr(obj, "REQUEST", None)
    if request is not None:
        message = _("msg_timestamp_removed")
        api.portal.show_message(message, request)


def publication_state_changed(publication, event):
    """Set effective_date if empty when "publish"."""
    # bypass if creating institution
    if event.transition is None:
        return

    if event.new_state.id == 'published':
        if publication.enable_timestamping:
            timestamper = ITimeStamper(publication)
            if timestamper.is_timestamped():
               cts_logger.info(f"Timestamp already generated for {publication.absolute_url()}. Updating it.")
               publication.timestamp = None
            timestamper.timestamp()
            cts_logger.info(f"Timestamp generated for {publication.absolute_url()}")
            api.portal.show_message(
                _cts("Timestamp file has been successfully generated and saved"),
                publication.REQUEST
            )
        if publication.EffectiveDate() == "None":
            publication.setEffectiveDate(DateTime())
            publication.reindexObject(idxs=["effective", "effectiveRange"])


def publication_will_be_removed(publication, event):
    """Raise if current user can not."""
    if not publication.is_power_user():
        api.portal.show_message(_("You must be publications power user to remove this element!"),
                                request=publication.REQUEST, type="error")
        raise Redirect(publication.REQUEST.get('HTTP_REFERER'))
