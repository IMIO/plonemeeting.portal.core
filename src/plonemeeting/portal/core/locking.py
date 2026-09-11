# -*- coding: utf-8 -*-
"""Serialization guard for meeting synchronizations.

A meeting import/sync is a long (13s to several minutes), non-idempotent
operation creating content in an institution's ``decisions`` folder. Two
concurrent runs both see "no Meeting with this plonemeeting_uid", both call
``api.content.create()``, and both rename their temporary uuid4 id towards the
*same* final id derived from the same title. That concurrent
uncatalog/recatalog churn on a single path is what leaves orphan rids behind
in the portal_catalog: ``uids[path]`` keeps only the last writer's rid while
``data[rid]``, ``paths[rid]`` and the index forward maps keep both. The orphan
still holds the object's UID in the UUIDIndex forward map, so every later
reindex is silently refused and the content becomes invisible to UID searches.

We therefore hold an exclusive, immediately committed ``plone.locking`` lock
on the decisions folder for the whole duration of a synchronization.
"""

from contextlib import contextmanager
from plone import api
from plone.locking.interfaces import ILockable
from plone.locking.interfaces import ILockSettings
from plone.locking.interfaces import LockType
from plonemeeting.portal.core import logger
from plonemeeting.portal.core.config import DEC_FOLDER_ID
from plonemeeting.portal.core.interfaces import IMeetingsFolder
from ZODB.POSException import ConflictError
from zope.component import adapter
from zope.interface import implementer

import transaction


#: Minutes. Must comfortably outlive the longest legitimate import (annexes
#: are downloaded serially), while staying short enough that a lock wedged by
#: a killed instance heals on its own without an operator.
SYNC_LOCK_TIMEOUT = 15

#: Exclusive lock held for the whole duration of a meeting synchronization.
#: ``stealable=False`` keeps Plone from ever offering an "Unlock" button for
#: it. ``user_unlockable=False`` makes ``can_safely_unlock()`` return False for
#: everybody, including the lock creator, which is what prevents
#: ``plone.locking.events.unlockAfterModification`` from dropping the lock when
#: somebody edits the folder mid-import.
SYNC_LOCK = LockType(
    "plonemeeting.portal.core.sync",
    stealable=False,
    user_unlockable=False,
    timeout=SYNC_LOCK_TIMEOUT,
)


@implementer(ILockSettings)
@adapter(IMeetingsFolder)
class MeetingsFolderLockSettings:
    """Make sync locking independent of the site-wide TTW edit-locking flag.

    ``TTWLockable.lock()`` starts with a ``queryAdapter(context, ILockSettings)``
    and silently returns without locking anything when ``lock_on_ttw_edit`` is
    False. That registry record is an editorial preference exposed in the
    Editing control panel; this lock is a data-integrity guard and must not be
    disableable from there.
    """

    lock_on_ttw_edit = True

    def __init__(self, context):
        self.context = context


class SyncAlreadyRunning(Exception):
    """A synchronization is already running on this decisions folder."""

    def __init__(self, lock_info=None):
        self.lock_info = lock_info or []
        super().__init__("A synchronization is already running")

    @property
    def creator(self):
        """Best effort human readable name of whoever holds the lock."""
        for info in self.lock_info:
            userid = info.get("creator")
            if not userid:
                continue
            member = api.user.get(userid=userid)
            if member is None:
                return userid
            return member.getProperty("fullname", "") or userid
        return "?"


def get_sync_lock_context(institution):
    """Return the object a synchronization lock is taken on."""
    return institution[DEC_FOLDER_ID]


def sync_lock_info(folder):
    """Return the SYNC_LOCK info held on p_folder, or None.

    ``ILockable.lock_info()`` already skips expired locks, so a lock whose
    timeout elapsed is reported as absent and needs no explicit cleanup.
    """
    for info in ILockable(folder).lock_info():
        if getattr(info.get("type"), "__name__", None) == SYNC_LOCK.__name__:
            return info
    return None


def release_sync_lock(folder):
    """Release the SYNC_LOCK held on p_folder, if any."""
    ILockable(folder).unlock(SYNC_LOCK, stealable_only=False)


def _acquire(folder):
    """Take the SYNC_LOCK on p_folder and publish it to the other instances."""
    lockable = ILockable(folder)
    if lockable.locked():
        raise SyncAlreadyRunning(lockable.lock_info())
    lockable.lock(SYNC_LOCK)
    # lock() returns None and is a silent no-op both when locking is disabled
    # and when any other lock is already present, so never assume it worked.
    if sync_lock_info(folder) is None:
        raise SyncAlreadyRunning(lockable.lock_info())
    # Commit now so the lock is visible to the other Zope instance behind the
    # load balancer: without this, a concurrent submission would not see it
    # until this whole (long) transaction commits, which is far too late.
    # Two truly simultaneous acquisitions write the same PersistentMapping,
    # which has no conflict resolution, so one of them raises ConflictError
    # right here, before any REST call and before any invokeFactory. The
    # publisher then replays that request, which reads the committed lock and
    # is refused cleanly.
    transaction.commit()


@contextmanager
def sync_lock(institution):
    """Serialize meeting synchronizations on p_institution's decisions folder.

    :raises SyncAlreadyRunning: when another synchronization holds the lock.
    """
    folder = get_sync_lock_context(institution)
    path = "/".join(folder.getPhysicalPath())
    _acquire(folder)
    logger.info("SYNC lock acquired on %s", path)
    released = False
    try:
        yield
    except ConflictError:
        # This import is doomed and the publisher is about to replay the whole
        # request. Drop the failed work, then release the lock in a fresh
        # transaction so the replay is not refused by our own leftover lock.
        released = True
        transaction.abort()
        try:
            release_sync_lock(folder)
            transaction.commit()
            logger.warning("SYNC lock on %s released after a ConflictError", path)
        except Exception:
            # Never mask the ConflictError: the lock expires on its own.
            logger.exception(
                "SYNC could not release the lock on %s after a ConflictError, "
                "it will expire in at most %s minutes",
                path,
                SYNC_LOCK_TIMEOUT,
            )
        raise
    finally:
        if not released:
            release_sync_lock(folder)
            logger.info("SYNC lock released on %s", path)
