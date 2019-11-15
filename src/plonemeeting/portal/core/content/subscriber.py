# -*- coding: utf-8 -*-

from plone import api

from plonemeeting.portal.core import _
from plonemeeting.portal.core.utils import create_faceted_folder
from plonemeeting.portal.core.utils import set_constrain_types


def handle_institution_creation(obj, event):
    institution_id = obj.id
    institution_title = obj.title
    group_id = "{0}-institution_managers".format(institution_id)
    group_title = "{0} Institution Managers".format(institution_title.encode("utf-8"))
    api.group.create(groupname=group_id, title=group_title)
    obj.manage_setLocalRoles(group_id, ["Editor", "Reader", "Contributor", "Reviewer"])
    create_faceted_folder(obj, _(u"Meetings"))
    create_faceted_folder(obj, _(u"Items"))
    # Unauthorize Folder creation in Institution now
    set_constrain_types(obj, ["Meeting"])
