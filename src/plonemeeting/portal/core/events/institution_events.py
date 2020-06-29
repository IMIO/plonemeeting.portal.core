from datetime import datetime

from Products.CMFPlone.controlpanel.browser.resourceregistry import (
    OverrideFolderManager,
)
from Products.CMFPlone.interfaces import IBundleRegistry
from plone.registry.interfaces import IRegistry
from plone import api
from zope.component import getUtility


def custom_css_needs_to_update(context, event):
    """
    This will update the custom css in plone_resources directory and
    in the registry when there is an event that create/modify an institution
    """

    # First, save the compiled in the plone_resources directory where static files are stored
    overrides = OverrideFolderManager(context)
    bundle_name = "plonemeeting.portal.core-custom"
    filepath = "static/%s-compiled.css" % bundle_name
    compiled_css = api.portal.get().unrestrictedTraverse("@@custom_colors.css").render()
    overrides.save_file(filepath, compiled_css)

    # Next, update the registry entry for the bundle
    registry = getUtility(IRegistry)
    bundles = registry.collectionOfInterface(
        IBundleRegistry, prefix="plone.bundles", check=False
    )
    bundle = bundles.get(bundle_name)
    if bundle:
        bundle.last_compilation = datetime.now()  # Used for cache busting
        bundle.csscompilation = "++plone++{}".format(filepath)
