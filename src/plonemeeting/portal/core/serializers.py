from plone.dexterity.interfaces import IDexterityContent
from plone.dexterity.utils import iterSchemata
from plone.restapi.interfaces import IFieldSerializer
from plone.restapi.serializer.converters import json_compatible
from plonemeeting.portal.core.interfaces import IInstitutionSerializeToJson
from zope.component import adapter, queryMultiAdapter
from zope.interface import implementer, Interface
from zope.schema import getFields


@implementer(IInstitutionSerializeToJson)
@adapter(IDexterityContent, Interface)
class InstitutionSerializerToJson:
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, fieldnames=["title"]):
        obj = self.context
        result = {
            "@id": obj.absolute_url(),
            "id": obj.id,
            "UID": obj.UID(),
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
