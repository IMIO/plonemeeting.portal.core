# -*- coding: utf-8 -*-

from Acquisition import aq_inner
from plone.app.layout.navigation.interfaces import INavtreeStrategy
from plone.app.layout.navigation.navtree import buildFolderTree
from Products.CMFPlone.browser.navigation import CatalogSiteMap
from Products.CMFPlone.browser.navtree import SitemapQueryBuilder
from zope.component import getMultiAdapter


class PortalSitemapQueryBuilder(SitemapQueryBuilder):
    """Override to force displaying portal_types "Folder" and "Institution"
       as it is set to only display "Folder" in the configuration because
       we use generated tabs on "Institution"."""

    def __init__(self, context):
        super(PortalSitemapQueryBuilder, self).__init__(context)
        self.query["portal_type"] = ("Folder", "Institution")


class PortalCatalogSiteMap(CatalogSiteMap):
    def siteMap(self):
        context = aq_inner(self.context)
        # begin change by plonemeeting.portal.core
        queryBuilder = PortalSitemapQueryBuilder(context)
        # end change by plonemeeting.portal.core
        query = queryBuilder()
        strategy = getMultiAdapter((context, self), INavtreeStrategy)

        return buildFolderTree(context, obj=context, query=query, strategy=strategy)
