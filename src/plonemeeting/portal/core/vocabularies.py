# -*- coding: utf-8 -*-
import copy

from plone import api
from plonemeeting.portal.core.content.institution import Institution
from z3c.form.interfaces import NO_VALUE
from zope.globalrequest import getRequest
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary
import json
import requests

from plonemeeting.portal.core.config import API_HEADERS, CATEGORY_IA_DELIB_FIELDS
from plonemeeting.portal.core.utils import format_meeting_date_and_state
from plonemeeting.portal.core.utils import get_api_url_for_meetings


class GlobalCategoryVocabularyFactory:
    def __call__(self, context):
        # use .copy() to make sure to return a copy of the record
        global_categories = api.portal.get_registry_record(
            name="plonemeeting.portal.core.global_categories"
        )
        if not global_categories:
            return SimpleVocabulary([])

        copy_of_categories = global_categories.copy()
        return SimpleVocabulary(
            [
                SimpleTerm(value=category_id, title=category_title)
                for category_id, category_title in copy_of_categories.items()
            ]
        )


GlobalCategoryVocabulary = GlobalCategoryVocabularyFactory()


class LocalCategoryVocabularyFactory:
    def __call__(self, context):
        req = getRequest()
        if context == NO_VALUE or isinstance(context, dict):
            institution = req.get('PUBLISHED').context
            if isinstance(institution, Institution) and hasattr(institution, "delib_categories"):
                local_categories = copy.deepcopy(institution.delib_categories)
                if local_categories:
                    return SimpleVocabulary(
                        [
                            SimpleTerm(value=category_id, title=category_title)
                            for category_id, category_title in local_categories
                        ]
                    )
        return GlobalCategoryVocabularyFactory()(context)


LocalCategoryVocabulary = LocalCategoryVocabularyFactory()


class MeetingDateVocabularyFactory:
    def __call__(self, context):
        institution = api.portal.get_navigation_root(context)
        brains = api.content.find(
            context=institution,
            portal_type="Meeting",
            sort_on="date_time",
            sort_order="descending",
        )
        terms = []
        for b in brains:
            title = format_meeting_date_and_state(b.date_time, b.review_state)
            term = SimpleVocabulary.createTerm(b.UID, b.UID, title)
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


class RemoteMeetingsVocabularyFactory:
    def __call__(self, context):
        institution = context
        url = get_api_url_for_meetings(institution)
        if not url:
            return SimpleVocabulary([])
        response = requests.get(
            url, auth=(institution.username, institution.password), headers=API_HEADERS
        )
        if response.status_code != 200:
            return SimpleVocabulary([])

        json_meetings = json.loads(response.text)
        return SimpleVocabulary(
            [
                SimpleTerm(value=elem["UID"], title=elem["title"])
                for elem in json_meetings.get("items", [])
            ]
        )


RemoteMeetingsVocabulary = RemoteMeetingsVocabularyFactory()


class DelibCategoryMappingFieldsVocabularyFactory:
    def __call__(self, context):
        mapping_field = copy.deepcopy(CATEGORY_IA_DELIB_FIELDS)
        return SimpleVocabulary(
            [
                SimpleTerm(value=field_id, title=field_name)
                for field_id, field_name in mapping_field
            ]
        )


DelibCategoryMappingFieldsVocabulary = DelibCategoryMappingFieldsVocabularyFactory()
