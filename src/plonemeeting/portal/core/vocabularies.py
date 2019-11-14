# -*- coding: utf-8 -*-
from plone import api
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


class MeetingDateVocabularyFactory:
    def __call__(self, context):
        institution = api.portal.get_navigation_root(context)
        brains = api.content.find(context=institution, portal_type="Meeting")
        terms = []
        for b in brains:
            term = SimpleVocabulary.createTerm(
                b.UID, b.UID, b.date_time.strftime("%d %B %Y (%H:%M)")
            )
            terms.append(term)
        return SimpleVocabulary(terms)


MeetingDateVocabulary = MeetingDateVocabularyFactory()


class RepresentativeVocabularyFactory:
    def __call__(self, context):
        institution = api.portal.get_navigation_root(context)
        mapping = institution.representatives_mappings
        return SimpleVocabulary(
            [
                SimpleTerm(
                    value=elem["representative_key"], title=elem["representative_value"]
                )
                for elem in mapping
            ]
        )


RepresentativeVocabulary = RepresentativeVocabularyFactory()
