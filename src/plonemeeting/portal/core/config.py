# -*- coding: utf-8 -*-
from plonemeeting.portal.core import _


CONFIG_FOLDER_ID = "config"
FACETED_DEC_FOLDER_ID = "faceted_decisions"
FACETED_DEC_XML_PATH = "faceted/config/decisions.xml"

FACETED_PUB_FOLDER_ID = "faceted_publications"
FACETED_PUB_XML_PATH = "faceted/config/publications.xml"

# appears in the URL so use french
DEC_FOLDER_ID = "decisions"
PUB_FOLDER_ID = "publications"

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
CATEGORY_IA_DELIB_FIELDS_MAPPING_EXTRA_INCLUDE = {
    "category": "categories",
    "classifier": "classifiers",
}

REPRESENTATIVE_IA_DELIB_FIELD = "groups_in_charge"


REGION_INS_CODE = "03000"
LOCATIONS_API_URL = "https://public.opendatasoft.com/api/records/1.0/search/?dataset=georef-belgium-municipality"

DEMO_INSTITUTION_IDS = ["belle-ville"]

FACETED_DEC_MANAGER_CRITERIA = ["annexes"]

FACETED_PUB_MANAGER_CRITERIA = ["annexes", "etat"]

DOCUMENTGENERATOR_GENERABLE_CONTENT_TYPES = ["Meeting", "Institution", "Item", "Publication", "Folder"]
DOCUMENTGENENATOR_USED_CONTENT_TYPES = ["ConfigurablePODTemplate", "PODTemplate", "StyleTemplate", "SubTemplate"]
DEFAULT_DOCUMENTGENERATOR_TEMPLATES = {
    "publication_notice": {
        "title": _("Publication notice"),
        "odt_file": "publication_notice.odt",
        "pod_formats": ["pdf"],
        "pod_portal_types": ["Publication"],
    },
    "publication_poster": {
        "title": _("Publication poster"),
        "odt_file": "publication_poster.odt",
        "pod_formats": ["pdf", "odt", "docx"],
        "pod_portal_types": ["Publication"],
    },
    "users_groups_summary_ods": {
        "title": _("Users and groups summary"),
        "odt_file": "users_groups_summary.ods",
        "pod_formats": ["ods", "xlsx"],
        "pod_portal_types": ["Institution"],
    },
    "users_groups_summary_odt": {
        "title": _("Users and groups summary"),
        "odt_file": "users_groups_summary.odt",
        "pod_formats": ["pdf", "odt", "docx"],
        "pod_portal_types": ["Institution"],
    },
}


MIMETYPE_TO_ICON = {
    "text/plain": {"icon": "bi bi-file-text", "color": "bg-light"},
    "text/html": {"icon": "bi bi-file-code", "color": "bg-yellow"},
    "text/css": {"icon": "bi bi-file-code", "color": "bg-blue"},
    "text/javascript": {"icon": "bi bi-file-code", "color": "bg-yellow"},
    "image/jpeg": {"icon": "bi bi-file-image", "color": "bg-grey"},
    "image/png": {"icon": "bi bi-file-image", "color": "bg-grey"},
    "image/gif": {"icon": "bi bi-file-image", "color": "bg-grey"},
    "image/svg+xml": {"icon": "bi bi-file-image", "color": "bg-red"},
    "application/pdf": {"icon": "bi bi-file-earmark-pdf", "color": "bg-red"},
    "application/msword": {"icon": "bi bi-file-earmark-word", "color": "bg-blue"},
    "application/vnd.ms-excel": {"icon": "bi bi-file-earmark-excel", "color": "bg-green"},
    "application/vnd.oasis.opendocument.text": {
        "icon": "bi bi-file-earmark-word",
        "color": "bg-blue",
    },
    "application/vnd.oasis.opendocument.spreadsheet": {
        "icon": "bi bi-file-earmark-excel",
        "color": "bg-green",
    },
    "application/vnd.oasis.opendocument.presentation": {
        "icon": "bi bi-file-earmark-slides",
        "color": "bg-yellow",
    },
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": {
        "icon": "bi bi-file-earmark-word",
        "color": "bg-blue",
    },
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
        "icon": "bi bi-file-earmark-excel",
        "color": "bg-green",
    },
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": {
        "icon": "bi bi-file-earmark-slides",
        "color": "bg-yellow",
    },
    "application/zip": {"icon": "bi bi-file-zip", "color": "bg-yellow"},
    "application/x-rar-compressed": {"icon": "bi bi-file-zip", "color": "bg-dark"},
    "audio/mpeg": {"icon": "bi bi-file-music", "color": "bg-dark"},
    "audio/wav": {"icon": "bi bi-file-music", "color": "bg-dark"},
    "audio/ogg": {"icon": "bi bi-file-music", "color": "bg-dark"},
    "video/mp4": {"icon": "bi bi-file-play", "color": "bg-dark"},
    "video/x-msvideo": {"icon": "bi bi-file-play", "color": "bg-dark"},
    "video/x-matroska": {"icon": "bi bi-file-play", "color": "bg-dark"},
    "application/json": {"icon": "bi bi-file-code", "color": "bg-red"},
    "application/xml": {"icon": "bi bi-file-code", "color": "bg-grey"},
    "application/javascript": {"icon": "bi bi-file-code", "color": "bg-yellow"},
    "application/x-shockwave-flash": {"icon": "bi bi-file", "color": "bg-red"},
    "application/x-tar": {"icon": "bi bi-file-zip", "color": "bg-grey"},
    "application/x-7z-compressed": {"icon": "bi bi-file-zip", "color": "bg-grey"},
    "application/x-bzip": {"icon": "bi bi-file-zip", "color": "bg-grey"},
    "application/x-bzip2": {"icon": "bi bi-file-zip", "color": "bg-grey"},
    "application/x-csh": {"icon": "bi bi-file-code", "color": "bg-grey"},
    "application/x-iso9660-image": {"icon": "bi bi-file-disc", "color": "bg-grey"},
    "application/vnd.apple.installer+xml": {"icon": "bi bi-file-code", "color": "bg-grey"},
    "application/vnd.mozilla.xul+xml": {"icon": "bi bi-file-code", "color": "bg-grey"},
    "application/x-httpd-php": {"icon": "bi bi-file-code", "color": "bg-grey"},
    "application/octet-stream": {"icon": "bi bi-file", "color": "bg-grey"},
    "font/woff": {"icon": "bi bi-file-font", "color": "bg-grey"},
    "font/woff2": {"icon": "bi bi-file-font", "color": "bg-grey"},
    "font/ttf": {"icon": "bi bi-file-font", "color": "bg-grey"},
    "font/otf": {"icon": "bi bi-file-font", "color": "bg-grey"},
    "application/x-font-ttf": {"icon": "bi bi-file-font", "color": "bg-grey"},
    "application/x-font-otf": {"icon": "bi bi-file-font", "color": "bg-grey"},
    "application/x-font-woff": {"icon": "bi bi-file-font", "color": "bg-grey"},
}
