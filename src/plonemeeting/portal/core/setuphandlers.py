# -*- coding: utf-8 -*-

from Products.CMFPlone.interfaces import INonInstallable
from datetime import datetime
from dateutil.relativedelta import relativedelta
from plone import api
from plone.api import content
from plone.app.textfield.value import RichTextValue
from plone.namedfile.file import NamedFile
from zope.i18n import translate
from zope.interface import implementer
import os

from plonemeeting.portal.core import _
from plonemeeting.portal.core.config import CONFIG_FOLDER_ID
from plonemeeting.portal.core.config import FACETED_FOLDER_ID
from plonemeeting.portal.core.utils import cleanup_contents
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
    current_lang = api.portal.get_current_language()[:2]
    portal = api.portal.get()
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
    faceted.unrestrictedTraverse("@@faceted_exportimport").import_xml(
        import_file=open(os.path.dirname(__file__) + faceted_config)
    )


def uninstall(context):
    """Uninstall script"""
    # Do something at the end of the uninstallation of this package.


def create_meeting(institution, date_time):
    title = date_time.strftime("%d %B %Y (%H:%M)")
    return content.create(
        container=institution,
        type="Meeting",
        title=title,
        date_time=date_time,
        attendees=u"Présents :\nMr XXX, Bourgmestre,\nMme YYYY, Échevine\n...",
    )


def create_file(container, filename):
    current_dir = os.path.abspath(os.path.dirname(__file__))
    file_path = os.path.join(current_dir, filename)
    if os.path.isfile(file_path):
        title = file_path.split(u"/")[-1]
        file_obj = content.create(container=container, type="File", title=title)
        fd = open(file_path, "rb")
        file_obj.file = NamedFile(
            data=fd, filename=title, contentType="application/pdf"
        )


def create_item(
    meeting,
    representative,
    category,
    title,
    number,
    deliberation,
    item_type,
    file_names=[],
):
    item = content.create(
        container=meeting,
        type="Item",
        title=title,
        number=number,
        representative=representative,
        category=category,
        deliberation=RichTextValue(deliberation, "text/html", "text/html"),
    )
    item.item_type = item_type

    for file_name in file_names:
        create_file(item, file_name)


def add_items_in_meeting(institution, meeting):
    fake_deliberation = (
        u"<p>Considérant qu’il y a lieu de XXXXXXXXXXXXXXXXXXXXX;</p>"
        u"<p>Vu la circulaire N° XXXXXXXXXXXXXXXXXXXXX;</p>"
        u"<p>Vu la proposition du directeur concerné de XXXXXXXXXXXXXXXXXXXX;</p>"
        u"<p>Vu le décret de XXXXXXXXXXXXXXXXXXXX en date du XX/XX/XXX;</p>"
        u"<p>Vu la loi du XX mai 1959 XXXXXXXXXXXXXXXXXXXXXXXXXXXXX;</p>"
        u"<p>Vu l’avis favorable de l’Échevin de la matière; </p>"
        u"<p>Le Conseil Communal <u><strong> DÉCIDE </strong > </u><strong>: </strong></p>"
        u"<p><em><strong>Article 1er </strong></em><strong> : </strong></p>"
        u"<p>Au scrutin secret et à l’unanimité, de XXXXXXXXXXXXXXXXXX.</p>"
        u"<p><em><strong>Article 2 </strong></em><strong> : </strong></p>"
        u"<p>XXXXXXXXXXXXXXXXXXXXXXXXX.</p>"
        u"<p><strong><em>Article 3</em> :</strong></p>"
        u"<p>La présente délibération sera soumise à la ratification du Conseil Communal. "
        u"Elle sera transmise à la direction concernée.</p>"
    )

    create_item(
        meeting=meeting,
        representative=institution.representatives_mappings[-1]["representative_key"],
        title=u"Premier point",
        number="1",
        item_type="normal",
        file_names=[u"profiles/demo/data/delibe-{}.pdf".format(institution.id)],
        category=institution.categories_mappings[-1]["local_category_id"],
        deliberation=fake_deliberation,
    )

    create_item(
        meeting=meeting,
        representative=institution.representatives_mappings[0]["representative_key"],
        title=u"Deuxième point",
        number="2",
        item_type="normal",
        category=institution.categories_mappings[0]["local_category_id"],
        deliberation=fake_deliberation,
    )

    create_item(
        meeting=meeting,
        representative=institution.representatives_mappings[0]["representative_key"],
        title=u"Point urgent",
        number="2.1",
        item_type="late",
        category=institution.categories_mappings[0]["local_category_id"],
        deliberation=fake_deliberation,
    )


def fill_demo_institution(institution):
    now = datetime.now()
    meeting1 = create_meeting(institution, now + relativedelta(months=-1))
    add_items_in_meeting(institution, meeting1)

    meeting2 = create_meeting(institution, now)
    add_items_in_meeting(institution, meeting2)

    meeting3 = create_meeting(institution, now + relativedelta(months=1))
    add_items_in_meeting(institution, meeting3)


def create_demo_content(context):
    """
    Initializes demo profile with demo content
    :param context:
    """
    portal = api.portal.get()
    city1 = getattr(portal, "city1", None)
    if not city1:
        city1 = content.create(
            container=portal, id="city1", type="Institution", title=u"City 1"
        )

    city2 = getattr(portal, "city2", None)
    if not city2:
        city2 = content.create(
            container=portal, id="city2", type="Institution", title=u"City 2"
        )

    city1.representatives_mappings = [
        {
            "representative_key": "zfz4ze6r4zg6zr4gze85",
            "representative_value": "Mr Canard",
            "representative_long_value": "Mr Canard Bourgmestre F.F.",
            "active": True,
        },
        {
            "representative_key": "ezab8qv5sv8sz54ev846",
            "representative_value": "Mr Lapinou",
            "representative_long_value": "Mme Coin Coin 1ère Échevin",
            "active": True,
        },
        {
            "representative_key": "zaefzg6ze5fd4ze6854s",
            "representative_value": "Mr Onizuka",
            "representative_long_value": "Mr Onizuka, Échevin de l'éducation",
            "active": True,
        },
    ]
    city1.categories_mappings = [
        {"global_category_id": "secretariat", "local_category_id": "administration"},
        {"global_category_id": "ecoles", "local_category_id": "education"},
    ]
    fill_demo_institution(city1)
    city2.representatives_mappings = [
        {
            "representative_key": "afezgf5ezd486ze4d",
            "representative_value": "Mme Lapine",
            "representative_long_value": "Mme Lapine Bourgmestre",
            "active": True,
        },
        {
            "representative_key": "zef687ezf4z68z7",
            "representative_value": "Mme Canard",
            "representative_long_value": "Mme Canard 1ère Échevine",
            "active": True,
        },
        {
            "representative_key": "loiuytrezdfg7",
            "representative_value": "Mr Mugiwara",
            "representative_long_value": "Mr Mugiwara, Échevin du tourisme",
            "active": True,
        },
    ]
    city2.categories_mappings = [
        {"global_category_id": "secretariat", "local_category_id": "administration"},
        {"global_category_id": "tourisme", "local_category_id": "tourisme"},
    ]
    fill_demo_institution(city2)
