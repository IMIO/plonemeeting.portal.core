from plone.dexterity.browser.view import DefaultView


class PublicationView(DefaultView):
    """
    """

    def get_effective_date(self):
        return self.context.effective_date.strftime('%d/%m/%Y %H:%M') \
            if self.context.effective_date else "-"

    def get_decision_date(self):
        return self.context.decision_date.strftime('%d/%m/%Y') \
            if self.context.decision_date else "-"

    def get_authority_date(self):
        return self.context.authority_date.strftime('%d/%m/%Y') \
            if self.context.authority_date else "-"
