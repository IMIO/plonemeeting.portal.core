# -*- coding: utf-8 -*-
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

from plonemeeting.portal.core import _

item_category = SimpleVocabulary(
    [
        SimpleTerm(value=u"locale", title=_(u"Locale")),
        SimpleTerm(value=u"globale", title=_(u"Globale")),
    ]
)

item_point_type = SimpleVocabulary(
    [
        SimpleTerm(value=u"normal", title=_(u"Normal")),
        SimpleTerm(value=u"significant", title=_(u"Significant")),
    ]
)
