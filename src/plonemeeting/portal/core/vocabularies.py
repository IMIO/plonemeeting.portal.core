# -*- coding: utf-8 -*-
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

from plonemeeting.portal.core import _


class CategoryVocabularyFactory:
    def __call__(self, context):
        return SimpleVocabulary(
            [
                SimpleTerm(value=u"local", title=_(u"Local category")),
                SimpleTerm(value=u"global", title=_(u"Global category")),
            ]
        )


CategoryVocabulary = CategoryVocabularyFactory()


class ItemTypeVocabularyFactory:
    def __call__(self, context):
        return SimpleVocabulary(
            [
                SimpleTerm(value=u"normal", title=_(u"Normal")),
                SimpleTerm(value=u"emergency", title=_(u"Emergency")),
            ]
        )


ItemTypeVocabulary = ItemTypeVocabularyFactory()
