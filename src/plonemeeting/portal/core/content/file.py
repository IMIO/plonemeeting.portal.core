# -*- coding: utf-8 -*-
from plone.app.contenttypes.interfaces import IFile
from plone.indexer.decorator import indexer
from zope.component import getMultiAdapter
from zope.globalrequest import getRequest


@indexer(IFile)
def get_icon(object):
    request = getRequest()
    if request is None:
        raise AttributeError
    utils_view = getMultiAdapter((object, request), name="file_view")
    icon = utils_view.get_mimetype_icon()
    return icon
