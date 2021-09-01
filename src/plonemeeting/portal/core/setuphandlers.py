# -*- coding: utf-8 -*-
from imio.helpers.content import richtextval
from plone import api
from plone.api import content
from plone.app.contenttypes.interfaces import IPloneAppContenttypesLayer
from plone.browserlayer.layer import mark_layer
from plone.i18n.normalizer.interfaces import IIDNormalizer
from plone.namedfile.file import NamedFile
from plonemeeting.portal.core import _
from plonemeeting.portal.core import logger
from plonemeeting.portal.core.config import APP_FOLDER_ID
from plonemeeting.portal.core.config import CONFIG_FOLDER_ID
from plonemeeting.portal.core.config import FACETED_FOLDER_ID
from plonemeeting.portal.core.config import FACETED_XML_PATH
from plonemeeting.portal.core.utils import cleanup_contents
from plonemeeting.portal.core.utils import create_faceted_folder
from plonemeeting.portal.core.utils import format_institution_managers_group_id
from plonemeeting.portal.core.utils import remove_left_portlets
from plonemeeting.portal.core.utils import remove_right_portlets
from Products.CMFPlone.interfaces import INonInstallable
from zope.component import getUtility
from zope.i18n import translate
from zope.interface import implementer
from zope.traversing.interfaces import BeforeTraverseEvent

import dateutil.parser
import json
import mimetypes
import os


@implementer(INonInstallable)
class HiddenProfiles(object):
    def getNonInstallableProfiles(self):
        """Hide uninstall profile from site-creation and quickinstaller."""
        return ["plonemeeting.portal.core:uninstall"]


def post_install(context):
    """Post install script"""
    portal = api.portal.get()
    current_lang = api.portal.get_default_language()[:2]

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
    faceted_config_path = os.path.join(os.path.dirname(__file__), FACETED_XML_PATH)
    with open(faceted_config_path, "rb") as faceted_config:
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
        contentType = mimetypes.guess_type(file_path)[0]
        title = os.path.basename(file_path)
        with open(file_path, "rb") as fd:
            file_obj = content.create(container=container, type="File", title=title)
            file_obj.file = NamedFile(
                data=fd, filename=title, contentType=contentType
            )


def create_demo_content(context):
    """
    Initializes demo profile with demo content
    :param context:
    """
    portal = api.portal.get()
    request = portal.REQUEST
    # make sure the plone.app.contenttypes BrowserLayer is enabled
    # because it is needed to create demo content (to get @@file_view)
    # when demo content added at Plone Site creation time
    # the plone.app.contenttypes BrowserLayer is not enabled
    if not IPloneAppContenttypesLayer.providedBy(request):
        logger.warning("IPloneAppContenttypesLayer not enabled on REQUEST, enabling it.")
        event = BeforeTraverseEvent(portal, request)
        mark_layer(portal, event)
    else:
        logger.info("IPloneAppContenttypesLayer already enabled on REQUEST.")

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
                categories_mappings=institution["categories_mappings"],
                representatives_mappings=institution["representatives_mappings"],
                plonemeeting_url=institution["plonemeeting_url"],
                username=institution["username"],
                password=institution["password"],
                meeting_config_id=institution["meeting_config_id"],
                meeting_filter_query=institution[
                    "meeting_filter_query"
                ],
                item_filter_query=institution[
                    "item_filter_query"
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

            for meeting in institution[APP_FOLDER_ID]:
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
                    decision = richtextval(item["decision"])
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
                    item_obj.formatted_title = richtextval("<p>" + item_obj.title + "</p>")
                    if "files" in item:
                        for file in item["files"]:
                            create_file(item_obj, file)
