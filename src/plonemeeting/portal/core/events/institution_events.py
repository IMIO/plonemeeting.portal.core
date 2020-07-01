from datetime import datetime

from Products.CMFPlone.controlpanel.browser.resourceregistry import (
    OverrideFolderManager,
)
from Products.CMFPlone.interfaces import IBundleRegistry
from plone.registry.interfaces import IRegistry
from plone import api
from zope.component import getUtility


def update_custom_css(context, event):
    """
    This will update the custom_colors.css in plone_resources directory and will update the bundle
    registry entry when there is an event that add or modify an institution.
    """
    # First, save the compiled css in the plone_resources directory where static files are stored
    overrides = OverrideFolderManager(context)
    bundle_name = "plonemeeting.portal.core-custom"
    filepath = "static/{0}-compiled.css".format(bundle_name)
    color_custom_css_view = api.portal.get().unrestrictedTraverse("@@custom_colors.css")
    compiled_css = color_custom_css_view()

    overrides.save_file(filepath, compiled_css)

    # Next, update the registry entry for the bundle
    registry = getUtility(IRegistry)
    bundles = registry.collectionOfInterface(
        IBundleRegistry, prefix="plone.bundles", check=False
    )
    bundle = bundles.get(bundle_name)
    if bundle:
        bundle.last_compilation = (  # Important : it's used for cache busting
            datetime.now()
        )
        bundle.csscompilation = "++plone++{}".format(filepath)
