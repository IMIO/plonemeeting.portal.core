# -*- coding: utf-8 -*-

from plonemeeting.portal.core import _


CONFIG_FOLDER_ID = "config"
FACETED_FOLDER_ID = "faceted"

CONTENTS_TO_CLEAN = ["Members", "events", "news"]

PLONEMEETING_API_MEETING_TYPE = "meeting"
PLONEMEETING_API_ITEM_TYPE = "item"

API_HEADERS = {"Content-type": "application/json", "Accept": "application/json"}

# keep those ids in translations files
REVIEW_STATES_IDS = [_(u"private"), _(u"in_project"), _(u"decision")]
