# -*- coding: utf-8 -*-
from plone import api
from plonemeeting.portal.core import _
from plonemeeting.portal.core.config import API_HEADERS
from plonemeeting.portal.core.config import CATEGORY_IA_DELIB_FIELDS
from plonemeeting.portal.core.content.institution import Institution
from plonemeeting.portal.core.utils import format_meeting_date_and_state
from plonemeeting.portal.core.utils import get_api_url_for_meetings
from z3c.form.interfaces import NO_VALUE
from zope.globalrequest import getRequest
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

import copy
import json
import requests


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
        if context == NO_VALUE or isinstance(context, dict):
            req = getRequest()
            institution = req.get('PUBLISHED').context
            if isinstance(institution, Institution):
                local_categories = copy.deepcopy(getattr(institution, 'delib_categories', {}))
                if local_categories:
                    return SimpleVocabulary(
                        [
                            SimpleTerm(value=category_id, title=local_categories[category_id])
                            for category_id in local_categories.keys()
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
    def __call__(self, context, representative_value_key='representative_value'):
        institution = api.portal.get_navigation_root(context)
        mapping = copy.deepcopy(getattr(institution, "representatives_mappings", []))
        representatives_mappings = [rpz for rpz in mapping if rpz['active']]
        disabled_representatives = [rpz for rpz in mapping if not rpz['active']]
        for rpz in disabled_representatives:
            rpz[representative_value_key] = _(u'(Passed term of office) ${representative_value}',
                                              mapping={'representative_value': rpz[representative_value_key]})
        mapping = representatives_mappings + disabled_representatives
        return SimpleVocabulary(
            [
                SimpleTerm(
                    value=elem["representative_key"], title=elem[representative_value_key]
                )
                for elem in mapping
            ]
        )


RepresentativeVocabulary = RepresentativeVocabularyFactory()


class LongRepresentativeVocabularyFactory(RepresentativeVocabularyFactory):
    def __call__(self, context):
        return super(LongRepresentativeVocabularyFactory, self).__call__(context, 'representative_long_value')


LongRepresentativeVocabulary = LongRepresentativeVocabularyFactory()


class EditableRepresentativeVocabularyFactory(RepresentativeVocabularyFactory):

    def __call__(self, context):
        if context == NO_VALUE or isinstance(context, dict):
            req = getRequest()
            institution = req.get('PUBLISHED').context
            if isinstance(institution, Institution):
                local_representatives = copy.deepcopy(getattr(institution, "delib_representatives", {}))
                if local_representatives:
                    return SimpleVocabulary(
                        [
                            SimpleTerm(value=representative_uid, title=local_representatives[representative_uid])
                            for representative_uid in local_representatives.keys()
                        ]
                    )
        return SimpleVocabulary([])


EditableRepresentativeVocabulary = EditableRepresentativeVocabularyFactory()


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


class InstitutionTypesVocabularyFactory:
    def __call__(self, context):
        institution_types = api.portal.get_registry_record(
            name="plonemeeting.portal.core.institution_types"
        )
        if not institution_types:
            return SimpleVocabulary([])

        return SimpleVocabulary(
            [
                SimpleTerm(value=id, title=title)
                for id, title in institution_types.items()
            ]
        )


InstitutionTypesVocabulary = InstitutionTypesVocabularyFactory()


class MeetingTypesVocabularyFactory:
    def __call__(self, context):
        meeting_types = api.portal.get_registry_record(
            name="plonemeeting.portal.core.meeting_types"
        )
        if not meeting_types:
            return SimpleVocabulary([])

        return SimpleVocabulary(
            [
                SimpleTerm(value=id, title=title)
                for id, title in meeting_types.items()
            ]
        )


MeetingTypesVocabulary = MeetingTypesVocabularyFactory()
