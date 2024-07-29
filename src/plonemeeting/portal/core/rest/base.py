from plone.restapi.services import Service


class PublicAPIView(Service):
    def check_permission(self):
        return True
