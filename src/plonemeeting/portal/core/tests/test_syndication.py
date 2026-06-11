# -*- coding: utf-8 -*-
from DateTime import DateTime
from plone import api
from plone.base.interfaces.syndication import IFeed
from plone.base.interfaces.syndication import IFeedSettings
from plonemeeting.portal.core.adapters import LatestItemsFolderFeed
from plonemeeting.portal.core.config import DEC_FOLDER_ID
from plonemeeting.portal.core.config import PUB_FOLDER_ID
from plonemeeting.portal.core.tests.portal_test_case import PmPortalDemoFunctionalTestCase
from zExceptions import NotFound
from zope.component import queryAdapter


class TestSyndication(PmPortalDemoFunctionalTestCase):
    """RSS/Atom feeds on the institution decisions and publications folders [DELIBE-255]"""

    def test_feeds_enabled_on_institution_folders_at_creation(self):
        self.login_as_admin()
        institution = api.content.create(container=self.portal, type="Institution", id="syndicated")
        self.assertTrue(IFeedSettings(institution[DEC_FOLDER_ID]).enabled)
        self.assertTrue(IFeedSettings(institution[PUB_FOLDER_ID]).enabled)
        # feeds are only enabled on the two listing folders, not anywhere else
        self.assertFalse(IFeedSettings(institution).enabled)

    def test_anonymous_can_read_feeds(self):
        self.logout()
        for folder_id in (DEC_FOLDER_ID, PUB_FOLDER_ID):
            folder = self.institution[folder_id]
            for feed_name in ("RSS", "rss.xml", "atom.xml"):
                feed = folder.restrictedTraverse(feed_name)()
                self.assertIn(folder.absolute_url(), feed)

    def test_feed_not_available_where_not_enabled(self):
        self.logout()
        with self.assertRaises(NotFound):
            self.institution.restrictedTraverse("rss.xml")()

    def test_feed_lists_latest_items_first(self):
        self.login_as_admin()
        folder = self.institution[PUB_FOLDER_ID]
        # create out of chronological order: the feed must sort on the
        # effective date, not on the creation (catalog) order
        # far enough in the future to stay within the feed limit
        for pub_id, days_from_now in (("older", 1000), ("newest", 3000), ("middle", 2000)):
            publication = api.content.create(container=folder, type="Publication", id=pub_id, title=pub_id)
            publication.setEffectiveDate(DateTime() + days_from_now)
            publication.reindexObject(idxs=["effective"])
        feed = queryAdapter(folder, IFeed)
        self.assertIsInstance(feed, LatestItemsFolderFeed)
        titles = [item.title for item in feed.items]
        self.assertLess(titles.index("newest"), titles.index("middle"))
        self.assertLess(titles.index("middle"), titles.index("older"))

    def test_rss_document_action_visible(self):
        rss_action = self.portal.portal_actions.document_actions.rss
        self.assertTrue(rss_action.visible)

    def test_syndication_util_context_enabled(self):
        folder = self.institution[PUB_FOLDER_ID]
        util = folder.restrictedTraverse("@@syndication-util")
        self.assertTrue(util.context_enabled())
        util = self.institution.restrictedTraverse("@@syndication-util")
        self.assertFalse(util.context_enabled())
