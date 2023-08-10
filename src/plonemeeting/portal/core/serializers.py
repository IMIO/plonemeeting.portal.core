import zope.i18n
from plone import api
from plone.dexterity.interfaces import IDexterityContent
from plone.dexterity.utils import iterSchemata
from plone.restapi.interfaces import IFieldSerializer
from plone.restapi.serializer.converters import json_compatible
from plonemeeting.portal.core.interfaces import IInstitutionSerializeToJson
from zope.component import adapter
from zope.component import queryMultiAdapter
from zope.interface import implementer
from zope.interface import Interface
from zope.schema import getFields


@implementer(IInstitutionSerializeToJson)
@adapter(IDexterityContent, Interface)
class InstitutionSerializerToJson:
    """
    Custom JSON serializer using the plone.restapi fields serializer
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, fieldnames=["title"]):
        """
        :param fieldnames: fieldnames to be serialized and included
        """
        obj = self.context
        state_id = api.content.get_state(obj)
        result = {
            "@id": obj.absolute_url(),
            "id": obj.id,
            "UID": obj.UID(),
            "review_state":  {
                "token":  state_id,
                "title": zope.i18n.translate(state_id, context=self.request, domain="plone")
            }
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
