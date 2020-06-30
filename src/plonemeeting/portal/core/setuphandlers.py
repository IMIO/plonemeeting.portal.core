# -*- coding: utf-8 -*-

from Products.CMFPlone.interfaces import INonInstallable
from plone import api
from plone.api import content
from plone.app.textfield.value import RichTextValue
from plone.i18n.normalizer.interfaces import IIDNormalizer
from plone.namedfile.file import NamedFile
from zope.component import getUtility
from zope.i18n import translate
from zope.interface import implementer

import dateutil.parser
import json
import os

from plonemeeting.portal.core import _
from plonemeeting.portal.core.config import CONFIG_FOLDER_ID
from plonemeeting.portal.core.config import FACETED_FOLDER_ID
from plonemeeting.portal.core.utils import (
    cleanup_contents,
    format_institution_managers_group_id,
)
from plonemeeting.portal.core.utils import create_faceted_folder
from plonemeeting.portal.core.utils import remove_left_portlets
from plonemeeting.portal.core.utils import remove_right_portlets


@implementer(INonInstallable)
class HiddenProfiles(object):
    def getNonInstallableProfiles(self):
        """Hide uninstall profile from site-creation and quickinstaller."""
        return ["plonemeeting.portal.core:uninstall"]


def post_install(context):
    """Post install script"""
    portal = api.portal.get()
    current_lang = api.portal.get_default_language()[:2]
    faceted_config = "/faceted/config/items.xml"

    if "config" in portal.objectIds():
        return

    remove_left_portlets()
    remove_right_portlets()
    cleanup_contents()

    # Create global config folder
    config_folder = api.content.create(
        container=portal,
        type="Folder",
        title=translate(_(u"Configuration folder"), target_language=current_lang),
        id=CONFIG_FOLDER_ID,
    )
    config_folder.exclude_from_nav = True

    # Create global faceted folder
    faceted = create_faceted_folder(
        config_folder,
        translate(_(u"Faceted"), target_language=current_lang),
        id=FACETED_FOLDER_ID,
    )
    subtyper = faceted.restrictedTraverse("@@faceted_subtyper")
    subtyper.enable()
    with open(os.path.dirname(__file__) + faceted_config, "rb") as faceted_config:
        faceted.unrestrictedTraverse("@@faceted_exportimport").import_xml(
            import_file=faceted_config
        )


def uninstall(context):
    """Uninstall script"""
    # Do something at the end of the uninstallation of this package.


def create_file(container, filename):
    current_dir = os.path.abspath(os.path.dirname(__file__))
    file_path = os.path.join(current_dir, "profiles/demo/data/", filename)
    if os.path.isfile(file_path):
        with open(file_path, "rb") as fd:
            title = file_path.split(u"/")[-1]
            file_obj = content.create(container=container, type="File", title=title)
            file_obj.file = NamedFile(
                data=fd, filename=title, contentType="application/pdf"
            )


def create_demo_content(context):
    """
    Initializes demo profile with demo content
    :param context:
    """
    portal = api.portal.get()
    current_dir = os.path.abspath(os.path.dirname(__file__))
    json_path = os.path.join(current_dir, "profiles/demo/data/data.json")

    with open(json_path) as json_str:
        data = json.load(json_str)
        api.portal.set_registry_record(
            "plonemeeting.portal.core.global_categories", data["categories"]
        )

        normalizer = getUtility(IIDNormalizer)
        for institution in data["institutions"]:
            institution_id = normalizer.normalize(institution["title"])
            institution_obj = content.create(
                container=portal,
                type="Institution",
                id=institution_id,
                title=institution["title"],
                representatives_mappings=institution["representatives_mappings"],
                plonemeeting_url=institution["plonemeeting_url"],
                username=institution["username"],
                password=institution["password"],
                meeting_config_id=institution["meeting_config_id"],
                additional_meeting_query_string_for_list=institution[
                    "additional_meeting_query_string_for_list"
                ],
                additional_published_items_query_string=institution[
                    "additional_published_items_query_string"
                ],
                item_decision_formatting_tal=institution[
                    "item_decision_formatting_tal"
                ],
                info_annex_formatting_tal=institution["info_annex_formatting_tal"],
            )
            content.transition(obj=institution_obj, transition="publish")

            user = api.user.create(
                username="{}-manager".format(institution_obj.id),
                email="noob@plone.org",
                password="supersecret",
            )

            group = api.group.get(format_institution_managers_group_id(institution_obj))
            group.addMember(user.id)

            for meeting in institution["meetings"]:
                date_time = dateutil.parser.parse(meeting["datetime"])
                meeting_obj = content.create(
                    container=institution_obj,
                    type="Meeting",
                    title=meeting["title"],
                    date_time=date_time,
                    plonemeeting_last_modified=dateutil.parser.parse(
                        meeting["plonemeeting_last_modified"]
                    ),
                )
                content.transition(obj=meeting_obj, transition="send_to_project")
                content.transition(obj=meeting_obj, transition="publish")

                for item in meeting["items"]:
                    decision = RichTextValue(item["decision"], "text/html", "text/html")
                    item_obj = content.create(
                        container=meeting_obj,
                        type="Item",
                        title=item["title"],
                        sortable_number=item["sortable_number"],
                        number=item["number"],
                        representatives_in_charge=item["representatives_in_charge"],
                        decision=decision,
                        category=item["category"],
                        plonemeeting_last_modified=dateutil.parser.parse(
                            meeting["plonemeeting_last_modified"]
                        ),
                    )

                    if "files" in item:
                        for file in item["files"]:
                            create_file(item_obj, file)
