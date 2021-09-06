# -*- coding: utf-8 -*-

from collective.pwexpiry.interfaces import ICustomPasswordValidator
from plonemeeting.portal.core import _
from zope.interface import implementer


@implementer(ICustomPasswordValidator)
class PloneMeetingPasswordValidator(object):
    def __init__(self, context):  # pragma: no cover
        self.context = context

    @staticmethod
    def validate(password, data):
        if len(password) < 8:
            return _(u"Passwords must be at least 8 characters in length.")
