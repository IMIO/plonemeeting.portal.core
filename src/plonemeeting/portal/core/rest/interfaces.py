from zope.interface import Interface


class IInstitutionSerializeToJson(Interface):
    """Adapter to serialize an Institution object into a JSON object."""

class IMeetingSerializeToJson(Interface):
    """Adapter to serialize an Meeting object into a JSON object."""

class IItemSerializeToJson(Interface):
    """Adapter to serialize an Item object into a JSON object."""
