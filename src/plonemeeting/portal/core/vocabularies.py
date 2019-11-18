# -*- coding: utf-8 -*-

from plone import api
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

from plonemeeting.portal.core import _


class GlobalCategoryVocabularyFactory:
    def __call__(self, context):
        global_categories = api.portal.get_registry_record(
            name="plonemeeting.portal.core.global_categories"
        )
        if not global_categories:
            return SimpleVocabulary([])
        return SimpleVocabulary(
            [
                SimpleTerm(value=category_id, title=category_title)
                for category_id, category_title in global_categories.items()
            ]
        )


GlobalCategoryVocabulary = GlobalCategoryVocabularyFactory()


class ItemTypeVocabularyFactory:
    def __call__(self, context):
        return SimpleVocabulary(
            [
                SimpleTerm(value=u"normal", title=_(u"Normal")),
                SimpleTerm(value=u"late", title=_(u"Emergency")),
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
        mapping = getattr(institution, "representatives_mappings", [])
        return SimpleVocabulary(
            [
                SimpleTerm(
                    value=elem["representative_key"], title=elem["representative_value"]
                )
                for elem in mapping
            ]
        )


RepresentativeVocabulary = RepresentativeVocabularyFactory()
