# -*- coding: utf-8 -*-
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

from plonemeeting.portal.core import _

item_category = SimpleVocabulary(
    [
        SimpleTerm(value=u"local", title=_(u"Local category")),
        SimpleTerm(value=u"global", title=_(u"Global category")),
    ]
)

item_point_type = SimpleVocabulary(
    [
        SimpleTerm(value=u"normal", title=_(u"Normal")),
        SimpleTerm(value=u"emergency", title=_(u"Emergency")),
    ]
)
