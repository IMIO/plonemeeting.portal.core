from IPython.testing.ipunittest import ipdoctest
from Products.CMFCore.utils import getToolByName
from plone.base.interfaces.controlpanel import ISiteSchema
from plone.protect.utils import addTokenToUrl
from plone.registry.interfaces import IRegistry
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.browsermenu.interfaces import IBrowserMenu
from zope.component import getUtility
from zope.contentprovider.interfaces import ITALNamespaceData
from zope.contentprovider.provider import ContentProviderBase
from zope.interface import implementer, Interface, provider
from zope.schema import Field
from plone.memoize.instance import memoize


@provider(ITALNamespaceData)
class IChangeStateButton(Interface):
    actual_context = Field("Provider context.", required=False)


@implementer(IChangeStateButton)
class ChangeStateButtonProvider(ContentProviderBase):
    """Content menu provider for the "view" tab: displays the menu"""

    index = ViewPageTemplateFile("change_state.pt")

    def update(self):
        if not hasattr(self, "actual_context") or self.actual_context is None:
            self.actual_context = self.context
        self.transitions = self._transitions()
        super().update()

    def render(self):
        return self.index()

    def _transitions(self):
        wf_tool = getToolByName(self.actual_context, "portal_workflow")
        transitions = wf_tool.listActionInfos(object=self.actual_context)
        res = []
        for t in transitions:
            if t["allowed"] and t["available"]:
                t["url"] = addTokenToUrl(t["url"], self.request)
                res.append(t)
        return res
