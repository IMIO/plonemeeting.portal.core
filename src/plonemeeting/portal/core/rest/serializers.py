from plone.dexterity.interfaces import IDexterityContent
from plone.dexterity.utils import iterSchemata
from plone.restapi.interfaces import IFieldSerializer
from plone.restapi.serializer.converters import json_compatible
from plonemeeting.portal.core.rest.interfaces import IInstitutionSerializeToJson
from plonemeeting.portal.core.rest.interfaces import IItemSerializeToJson
from plonemeeting.portal.core.rest.interfaces import IMeetingSerializeToJson
from zope.component import adapter
from zope.component import queryMultiAdapter
from zope.interface import implementer
from zope.interface import Interface
from zope.schema import getFields


class FlexibleSerializer:
    """
    Custom JSON serializer using the plone.restapi fields serializer
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, fieldnames=[]):
        """
        :param fieldnames: fieldnames to be serialized and included
        TODO: verify why title and description can't be used in fieldnames
        """
        obj = self.context
        result = {
            "@id": obj.absolute_url(),
            "id": obj.id,
            "UID": obj.UID(),
            "title": obj.title
        }
        for schema in iterSchemata(self.context):
            for name, field in getFields(schema).items():
                if name not in fieldnames:
                    continue
                # serialize the field
                serializer = queryMultiAdapter((field, obj, self.request), IFieldSerializer)
                value = serializer()
                result[json_compatible(name)] = value

        return result


@implementer(IInstitutionSerializeToJson)
@adapter(IDexterityContent, Interface)
class InstitutionSerializerToJson(FlexibleSerializer):
    """
    """


@implementer(IMeetingSerializeToJson)
@adapter(IDexterityContent, Interface)
class MeetingSerializerToJson(FlexibleSerializer):
    """
    """


@implementer(IItemSerializeToJson)
@adapter(IDexterityContent, Interface)
class ItemSerializerToJson(FlexibleSerializer):
    """
    """
