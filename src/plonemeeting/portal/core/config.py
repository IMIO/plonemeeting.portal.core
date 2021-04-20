# -*- coding: utf-8 -*-
from plonemeeting.portal.core import _

CONFIG_FOLDER_ID = "config"
FACETED_FOLDER_ID = "faceted"

CONTENTS_TO_CLEAN = ["Members", "events", "news"]

PLONEMEETING_API_MEETING_TYPE = "meeting"
PLONEMEETING_API_ITEM_TYPE = "item"

API_HEADERS = {"Content-type": "application/json", "Accept": "application/json"}

# keep those ids in translations files
REVIEW_STATES_IDS = [_("private"), _("in_project"), _("decision")]

DEFAULT_CATEGORY_IA_DELIB_FIELD = "category"
CATEGORY_IA_DELIB_FIELDS = (
    ("category", _("category")),
    ("classifier", _("classifier")),
)
