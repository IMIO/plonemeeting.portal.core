# -*- coding: utf-8 -*-
from plone import api
from plonemeeting.portal.core import _
from plonemeeting.portal.core import plone_
from plonemeeting.portal.core.config import API_HEADERS
from plonemeeting.portal.core.config import CATEGORY_IA_DELIB_FIELDS
from plonemeeting.portal.core.config import DEC_FOLDER_ID
from plonemeeting.portal.core.config import DOCUMENTGENERATOR_GENERABLE_CONTENT_TYPES
from plonemeeting.portal.core.config import PUB_FOLDER_ID
from plonemeeting.portal.core.content.institution import Institution
from plonemeeting.portal.core.utils import format_meeting_date_and_state
from plonemeeting.portal.core.utils import get_api_url_for_meetings
from plonemeeting.portal.core.utils import get_context_from_request
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

import copy
import json
import requests


class EnabledTabsVocabularyFactory:
    def __call__(self, context):
        return SimpleVocabulary(
            (
                SimpleTerm(value=DEC_FOLDER_ID, title=_(DEC_FOLDER_ID.capitalize())),
                SimpleTerm(value=PUB_FOLDER_ID, title=_(PUB_FOLDER_ID.capitalize())),
            ),
        )


EnabledTabsVocabulary = EnabledTabsVocabularyFactory()


class PublicationsPowerUsersVocabularyFactory:
    def __call__(self, context):
        return SimpleVocabulary(
            (
                SimpleTerm(value="gbastien", title="Gauthier Bastien"),
                SimpleTerm(value="gbastien2", title="Gauthier Bastien2"),
            ),
        )


PublicationsPowerUsersVocabulary = PublicationsPowerUsersVocabularyFactory()


class GlobalCategoryVocabularyFactory:
    def __call__(self, context):
        # use .copy() to make sure to return a copy of the record
        global_categories = api.portal.get_registry_record(name="plonemeeting.portal.core.global_categories")
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
        if context is None:
            context = get_context_from_request()
        if isinstance(context, Institution):
            local_categories = copy.deepcopy(getattr(context, "delib_categories", {}))
            if local_categories:
                return SimpleVocabulary(
                    [
                        SimpleTerm(value=category_id, title=local_categories[category_id])
                        for category_id in local_categories.keys()
                    ]
                )
        return GlobalCategoryVocabularyFactory()(context)


LocalCategoryVocabulary = LocalCategoryVocabularyFactory()


class DocumentTypesVocabularyFactory:
    def __call__(self, context):
        # use .copy() to make sure to return a copy of the record
        document_types = api.portal.get_registry_record(name="plonemeeting.portal.core.document_types")
        if not document_types:
            return SimpleVocabulary([])

        return SimpleVocabulary(
            [
                SimpleTerm(value=doc_type_id, title=doc_type_title)
                for doc_type_id, doc_type_title in document_types.copy().items()
            ]
        )


DocumentTypesVocabulary = DocumentTypesVocabularyFactory()


class LegislativeAuthoritiesVocabularyFactory:
    def __call__(self, context):
        # use .copy() to make sure to return a copy of the record
        legislative_authorities = api.portal.get_registry_record(
            name="plonemeeting.portal.core.legislative_authorities"
        )
        if not legislative_authorities:
            return SimpleVocabulary([])

        return SimpleVocabulary(
            [
                SimpleTerm(value=leg_auth_id, title=leg_auth_title)
                for leg_auth_id, leg_auth_title in legislative_authorities.copy().items()
            ]
        )


LegislativeAuthoritiesVocabulary = LegislativeAuthoritiesVocabularyFactory()


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
    def __call__(self, context, representative_value_key="representative_value"):
        institution = api.portal.get_navigation_root(context)
        mapping = copy.deepcopy(getattr(institution, "representatives_mappings", [])) or []
        representatives_mappings = [rpz for rpz in mapping if rpz["active"]]
        disabled_representatives = [rpz for rpz in mapping if not rpz["active"]]
        for rpz in disabled_representatives:
            rpz[representative_value_key] = _(
                "(Passed term of office) ${representative_value}",
                mapping={"representative_value": rpz[representative_value_key]},
            )
        mapping = representatives_mappings + disabled_representatives
        return SimpleVocabulary(
            [SimpleTerm(value=elem["representative_key"], title=elem[representative_value_key]) for elem in mapping]
        )


RepresentativeVocabulary = RepresentativeVocabularyFactory()


class LongRepresentativeVocabularyFactory(RepresentativeVocabularyFactory):
    def __call__(self, context):
        return super(LongRepresentativeVocabularyFactory, self).__call__(context, "representative_long_value")


LongRepresentativeVocabulary = LongRepresentativeVocabularyFactory()


class EditableRepresentativeVocabularyFactory(RepresentativeVocabularyFactory):

    def __call__(self, context):
        if context is None:
            context = get_context_from_request()
        if isinstance(context, Institution):
            local_representatives = copy.deepcopy(getattr(context, "delib_representatives", {}))
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
        response = requests.get(url, auth=(institution.username, institution.password), headers=API_HEADERS)
        if response.status_code != 200:
            return SimpleVocabulary([])

        json_meetings = json.loads(response.text)
        return SimpleVocabulary(
            [SimpleTerm(value=elem["UID"], title=elem["title"]) for elem in json_meetings.get("items", [])]
        )


RemoteMeetingsVocabulary = RemoteMeetingsVocabularyFactory()


class DelibCategoryMappingFieldsVocabularyFactory:
    def __call__(self, context):
        mapping_field = copy.deepcopy(CATEGORY_IA_DELIB_FIELDS)
        return SimpleVocabulary(
            [SimpleTerm(value=field_id, title=field_name) for field_id, field_name in mapping_field]
        )


DelibCategoryMappingFieldsVocabulary = DelibCategoryMappingFieldsVocabularyFactory()


class InstitutionTypesVocabularyFactory:
    def __call__(self, context):
        institution_types = api.portal.get_registry_record(name="plonemeeting.portal.core.institution_types")
        if not institution_types:
            return SimpleVocabulary([])

        return SimpleVocabulary([SimpleTerm(value=id, title=title) for id, title in institution_types.items()])


InstitutionTypesVocabulary = InstitutionTypesVocabularyFactory()


class MeetingTypesVocabularyFactory:
    def __call__(self, context):
        meeting_types = api.portal.get_registry_record(name="plonemeeting.portal.core.meeting_types")
        if not meeting_types:
            return SimpleVocabulary([])

        return SimpleVocabulary([SimpleTerm(value=id, title=title) for id, title in meeting_types.items()])


MeetingTypesVocabulary = MeetingTypesVocabularyFactory()


class PublicationReviewStatesVocabularyFactory:
    def __call__(self, context):
        wf = api.portal.get_tool("portal_workflow").getWorkflowsFor("Publication")[0]
        return SimpleVocabulary(
            [SimpleTerm(value=state_id, title=plone_(state.title)) for state_id, state in wf.states.items()]
        )


PublicationReviewStatesVocabulary = PublicationReviewStatesVocabularyFactory()


class InstitutionManageableGroupsVocabularyFactory:
    def __call__(self, context):
        """
        Return a vocabulary of groups that can be managed by the current institution.
        """
        group_tool = api.portal.get_tool("portal_groups")
        all_groups = group_tool.listGroups()
        items = []
        for group in all_groups:
            gid = group.getId()
            if gid.startswith(f"{context.id}-") and "members" not in gid:
                items.append(SimpleTerm(value=gid, title=group.getProperty("title")))

        return SimpleVocabulary(items)


InstitutionManageableGroupsVocabulary = InstitutionManageableGroupsVocabularyFactory()


class TemplatesContentTypesVocabularyFactory(object):
    """
    Vocabulary factory for 'pod_portal_types' field.
    """

    def __call__(self, context):
        vocabulary = SimpleVocabulary([SimpleTerm(p, p, p) for p in DOCUMENTGENERATOR_GENERABLE_CONTENT_TYPES])
        return vocabulary


TemplatesContentTypesVocabulary = TemplatesContentTypesVocabularyFactory()


class InstitutionTemplatesVocabularyFactory:
    def __call__(self, context):
        """
        Return a vocabulary of templates for the current institution.
        """
        portal = api.portal.get()
        institution = api.portal.get_navigation_root(context)
        common_templates_folder = portal.restrictedTraverse("config/templates")
        institution_templates_folder = getattr(institution, "templates", {})
        vocabulary = []
        for template in common_templates_folder.values():
            vocabulary.append(SimpleTerm(value=template.getId(), title=template.Title()))
        for template in institution_templates_folder.values():
            vocabulary.append(
                SimpleTerm(
                    value=f"{institution.getId()}__{template.getId()}", title="Institution - " + template.Title()
                )
            )
        return SimpleVocabulary(vocabulary)


InstitutionTemplatesVocabulary = InstitutionTemplatesVocabularyFactory()


class InstitutionAllAndTemplatesVocabularyFactory(InstitutionTemplatesVocabularyFactory):
    def __call__(self, context):
        """
        Return a vocabulary of templates for the current institution with an 'All' entry.
        """
        if context is None:
            context = get_context_from_request()
        vocabulary = super(InstitutionAllAndTemplatesVocabularyFactory, self).__call__(context)
        all_term = SimpleTerm(value="__all__", title=_("All templates"))
        terms = [all_term] + list(vocabulary)
        return SimpleVocabulary(terms)


InstitutionAllAndTemplatesVocabulary = InstitutionAllAndTemplatesVocabularyFactory()


class InstitutionTemplateSettingsVocabularyFactory:
    def __call__(self, context):
        template_settings = copy.deepcopy(
            api.portal.get_registry_record(name="plonemeeting.portal.core.template_settings")
        )
        vocabulary = []
        for key, value in template_settings.items():
            vocabulary.append(SimpleTerm(value=key, title=f"{value} [{key}]"))
        return SimpleVocabulary(vocabulary)


InstitutionTemplateSettingsVocabulary = InstitutionTemplateSettingsVocabularyFactory()
