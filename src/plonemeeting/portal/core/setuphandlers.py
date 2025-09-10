# -*- coding: utf-8 -*-
from collective.exportimport.import_content import ImportContent
from imio.helpers.content import richtextval
from plone import api
from plone.api import content
from plone.app.contenttypes.interfaces import IPloneAppContenttypesLayer
from plone.browserlayer.layer import mark_layer
from plone.i18n.normalizer.interfaces import IIDNormalizer
from plone.namedfile.file import NamedBlobFile
from plone.namedfile.file import NamedFile
from plonemeeting.portal.core import _
from plonemeeting.portal.core import logger
from plonemeeting.portal.core.config import CONFIG_FOLDER_ID
from plonemeeting.portal.core.config import DEC_FOLDER_ID
from plonemeeting.portal.core.config import DEFAULT_DOCUMENTGENERATOR_TEMPLATES
from plonemeeting.portal.core.config import DOCUMENTGENENATOR_USED_CONTENT_TYPES
from plonemeeting.portal.core.config import FACETED_DEC_FOLDER_ID
from plonemeeting.portal.core.config import FACETED_DEC_XML_PATH
from plonemeeting.portal.core.config import FACETED_PUB_FOLDER_ID
from plonemeeting.portal.core.config import FACETED_PUB_XML_PATH
from plonemeeting.portal.core.interfaces import IPlonemeetingPortalConfigFolder
from plonemeeting.portal.core.utils import cleanup_contents
from plonemeeting.portal.core.utils import create_faceted_folder
from plonemeeting.portal.core.utils import create_templates_folder
from plonemeeting.portal.core.utils import get_decisions_managers_group_id
from plonemeeting.portal.core.utils import get_publications_managers_group_id
from plonemeeting.portal.core.utils import remove_left_portlets
from plonemeeting.portal.core.utils import remove_right_portlets
from plonemeeting.portal.core.utils import set_constrain_types
from Products.CMFPlone.interfaces import INonInstallable
from zope.component import getUtility
from zope.i18n import translate
from zope.interface import alsoProvides
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
    alsoProvides(config_folder, IPlonemeetingPortalConfigFolder)
    config_folder.exclude_from_nav = True

    # Create global meetings and publications faceted folders
    for faceted_folder_id, faceted_folder_title, faceted_xml_path in (
            (FACETED_DEC_FOLDER_ID, _("Faceted decisions"), FACETED_DEC_XML_PATH),
            (FACETED_PUB_FOLDER_ID, _("Faceted publications"), FACETED_PUB_XML_PATH)):
        faceted = create_faceted_folder(
            config_folder,
            translate(faceted_folder_title, target_language=current_lang),
            id=faceted_folder_id,
        )

        faceted_config_path = os.path.join(os.path.dirname(__file__), faceted_xml_path)
        with open(faceted_config_path, "rb") as faceted_config:
            faceted.unrestrictedTraverse("@@faceted_exportimport").import_xml(
                import_file=faceted_config
            )

    # Create the global templates folder
    if not config_folder.get("templates"):
        create_templates_folder(config_folder)
    templates_folder = config_folder.get("templates")

    # Add default templates to it
    for key, template in DEFAULT_DOCUMENTGENERATOR_TEMPLATES.items():
        logger.info(f"Adding default template {key} to templates folder")
        create_or_update_default_template(templates_folder, key, **template)

def uninstall(context):
    """Uninstall script"""
    # Do something at the end of the uninstallation of this package.


def create_file(container, filename):
    current_dir = os.path.abspath(os.path.dirname(__file__))
    file_path = os.path.join(current_dir, "profiles/demo/data/", filename)
    if os.path.isfile(file_path):
        content_type = mimetypes.guess_type(file_path)[0]
        title = os.path.basename(file_path)
        with open(file_path, "rb") as fd:
            file_obj = content.create(container=container, type="File", title=title)
            file_obj.file = NamedFile(
                data=fd, filename=title, contentType=content_type
            )


def create_or_update_default_template(container, template_id, title="", odt_file=None, pod_formats=None, pod_portal_types=None):
    """
    Create or update a default template in the templates folder.
    """
    current_dir = os.path.abspath(os.path.dirname(__file__))
    file_path = os.path.join(current_dir, "profiles/default/templates/", odt_file)
    i18n_title = translate(title, target_language=api.portal.get_default_language()[:2])
    with open(file_path, "rb") as fd:
        data = fd.read()
    if template_id in container.objectIds():
        template = container[template_id]
        template.title = i18n_title
        template.odt_file = NamedBlobFile(
            data=data,
            contentType=mimetypes.guess_type(odt_file)[0],
            filename=template_id,
        )
        if pod_formats is not None:
            template.pod_formats = pod_formats
        if pod_portal_types is not None:
            template.pod_portal_types = pod_portal_types
    else:
        api.content.create(
            type="ConfigurablePODTemplate",
            id=template_id,
            title=i18n_title,
            odt_file=NamedBlobFile(
                data=data,
                contentType=mimetypes.guess_type(odt_file)[0],
                filename=template_id,
            ),
            pod_formats=pod_formats,
            pod_portal_types=pod_portal_types,
            container=container,
            exclude_from_nav=True,
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
        api.portal.set_registry_record(
            "plonemeeting.portal.core.document_types", data["document_types"]
        )
        api.portal.set_registry_record(
            "plonemeeting.portal.core.legislative_authorities",
            data["legislative_authorities"]
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
            decisions_manager = api.user.create(
                username="{}-decisions-manager".format(institution_obj.id),
                email="noob@plone.org",
                password="supersecret",
            )
            publications_manager = api.user.create(
                username="{}-publications-manager".format(institution_obj.id),
                email="noob@plone.org",
                password="supersecret",
            )
            group = api.group.get(get_decisions_managers_group_id(institution_obj))
            group.addMember(decisions_manager.id)
            group = api.group.get(get_publications_managers_group_id(institution_obj))
            group.addMember(publications_manager.id)

            meetings_container = institution_obj.get(DEC_FOLDER_ID)
            for meeting in institution["meetings"]:
                date_time = dateutil.parser.parse(meeting["datetime"])
                meeting_obj = content.create(
                    container=meetings_container,
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

            create_demo_publications(portal, institution_obj)

        faqs = content.create(
            container=portal,
            type="Folder",
            title="Foire aux questions",
            id="faq"
        )
        for faq in data["faqs"]:
            document = content.create(
                container=faqs,
                type="Document",
                title=faq.get("title"),
                id=faq.get("id"),
                text=richtextval(faq["text"])
            )
            content.transition(obj=document, transition="publish")
    brain = content.find(context=portal, id='front-page')
    if brain:
        default_front_page = content.get(UID=brain[0].UID)
        content.delete(default_front_page)

    portal.portal_workflow.updateRoleMappings()


def create_demo_publications(portal, context):
    current_dir = os.path.abspath(os.path.dirname(__file__))

    with open(os.path.join(current_dir, "profiles/demo/data/publications.json"), "r") as f:
        pub_data = json.load(f)
        for item in pub_data:  # We need to specify a custom @id otherwise exportimport doesn't work
            item["@id"] = "/".join(portal.getPhysicalPath() + (context.id, "publications", item["@id"]))
    request = getattr(context, "REQUEST", None)

    if request is None:
        request = portal.REQUEST
    import_content = ImportContent(context.publications, request)

    import_content.handle_existing_content = 1  # Replace
    import_content.limit = None
    import_content.commit = None
    import_content.import_old_revisions = False
    import_content.import_to_current_folder = True
    # We need to use `import_new_content` instead of `do_import` to avoid commiting
    # because it breaks test layers
    import_content.import_new_content(pub_data)
