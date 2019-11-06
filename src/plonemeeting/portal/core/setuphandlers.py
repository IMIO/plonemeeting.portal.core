# -*- coding: utf-8 -*-
import os
from datetime import datetime

from Products.CMFPlone.interfaces import INonInstallable
from dateutil.relativedelta import relativedelta
from plone import api
from plone.api import content
from plone.app.textfield.value import RichTextValue
from plone.namedfile.file import NamedFile
from zope.interface import implementer


@implementer(INonInstallable)
class HiddenProfiles(object):
    def getNonInstallableProfiles(self):
        """Hide uninstall profile from site-creation and quickinstaller."""
        return ["plonemeeting.portal.core:uninstall"]


def post_install(context):
    """Post install script"""
    # Do something at the end of the installation of this package.


def uninstall(context):
    """Uninstall script"""
    # Do something at the end of the uninstallation of this package.


def create_meeting(institution, meeting_datetime):
    title = meeting_datetime.strftime("%d %B %Y (%H:%M)")
    return content.create(
        container=institution,
        type="Meeting",
        title=title,
        meeting_datetime=meeting_datetime,
        attendees=u"Présents :\nMr XXX, Bourgmestre,\nMme YYYY, Échevine\n...",
    )


def create_file(container, filename):
    current_dir = os.path.abspath(os.path.dirname(__file__))
    file_path = os.path.join(current_dir, filename)
    if os.path.isfile(file_path):
        title = file_path.split(u"/")[-1]
        file_obj = content.create(container=container, type="File", title=title)
        fd = open(file_path, "r")
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


def create_demo_content(context):
    """
    Initializes demo profile with demo content
    :param context:
    """
    portal = api.portal.get()
    liege = getattr(portal, "liege", None)
    if not liege:
        liege = content.create(
            container=portal, id="liege", type="Institution", title=u"Liège"
        )

    namur = getattr(portal, "namur", None)
    if not namur:
        namur = content.create(
            container=portal, id="namur", type="Institution", title=u"Namur"
        )

    liege.representatives_mappings = [
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
    liege.categories_mappings = [
        {"global_category_id": "secretariat", "local_category_id": "administration"},
        {"global_category_id": "ecoles", "local_category_id": "education"},
    ]
    namur.representatives_mappings = [
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

    fake_deliberation = (
        u"<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do "
        u"eiusmod tempor incididunt ut labore et dolore magna aliqua. Vulputate "
        u"dignissim suspendisse in est. Vitae tempus quam pellentesque nec. "
        u"Tellus integer feugiat scelerisque varius morbi enim. Facilisi nullam "
        u"vehicula ipsum a arcu cursus vitae. Vestibulum rhoncus est pellentesque "
        u"elit. Fringilla ut morbi tincidunt augue interdum velit. Diam "
        u"sollicitudin tempor id eu nisl nunc mi ipsum faucibus. Massa placerat "
        u"duis ultricies lacus sed turpis tincidunt. Nulla malesuada pellentesque "
        u"elit eget gravida cum sociis natoque.</p><p>Elementum eu facilisis sed "
        u"odio morbi quis commodo. Consectetur lorem donec massa sapien. Tempus "
        u"iaculis urna id volutpat lacus laoreet non curabitur. In eu mi bibendum "
        u"neque egestas congue quisque egestas. Scelerisque fermentum dui "
        u"faucibus in ornare quam viverra orci sagittis. Lacus luctus accumsan "
        u"tortor posuere ac ut consequat. Odio ut sem nulla pharetra. Condimentum "
        u"mattis pellentesque id nibh tortor id. Tincidunt augue interdum velit "
        u"euismod in pellentesque. Ornare quam viverra orci sagittis. "
        u"Sollicitudin tempor id eu nisl nunc mi ipsum faucibus vitae. Nunc "
        u"consequat interdum varius sit amet mattis. Et netus et malesuada fames "
        u"ac turpis egestas.</p><p>Sed viverra tellus in hac habitasse platea "
        u"dictumst vestibulum. Enim nulla aliquet porttitor lacus luctus accumsan "
        u"tortor posuere. Viverra orci sagittis eu volutpat odio facilisis "
        u"mauris. Elementum eu facilisis sed odio morbi quis commodo odio. Eu "
        u"facilisis sed odio morbi quis commodo odio. Consectetur purus ut "
        u"faucibus pulvinar elementum integer. Integer vitae justo eget magna. "
        u"Pulvinar neque laoreet suspendisse interdum consectetur libero id "
        u"faucibus nisl. Vehicula ipsum a arcu cursus vitae congue mauris "
        u"rhoncus. Vulputate mi sit amet mauris commodo. Maecenas ultricies mi "
        u"eget mauris pharetra et ultrices neque ornare. Arcu cursus vitae congue "
        u"mauris rhoncus aenean. Non sodales neque sodales ut etiam sit. "
        u"Adipiscing elit ut aliquam purus sit amet. Ac auctor augue mauris augue "
        u"neque gravida in fermentum. Senectus et netus et malesuada fames ac "
        u"turpis egestas maecenas. Amet nulla facilisi morbi tempus iaculis urna "
        u"id volutpat. Felis eget velit aliquet sagittis id. Leo integer "
        u"malesuada nunc vel risus.</p><p>Dolor sit amet consectetur adipiscing "
        u"elit. In est ante in nibh mauris cursus mattis molestie a. Ut venenatis "
        u"tellus in metus vulputate eu scelerisque felis. Vitae aliquet nec "
        u"ullamcorper sit amet risus nullam eget felis. Aliquam sem et tortor "
        u"consequat id. Nibh tortor id aliquet lectus. Blandit aliquam etiam erat "
        u"velit scelerisque in dictum non consectetur. Varius quam quisque id "
        u"diam vel quam elementum. Lorem donec massa sapien faucibus et molestie. "
        u"At auctor urna nunc id. Id diam maecenas ultricies mi eget mauris "
        u"pharetra et ultrices. Risus ultricies tristique nulla aliquet enim "
        u"tortor at. Suspendisse interdum consectetur libero id. Egestas "
        u"fringilla phasellus faucibus scelerisque eleifend donec pretium "
        u"vulputate sapien. Amet aliquam id diam maecenas ultricies mi eget "
        u"mauris pharetra. Amet consectetur adipiscing elit ut aliquam "
        u"purus.</p><p>Duis tristique sollicitudin nibh sit amet commodo. Sit "
        u"amet mattis vulputate enim nulla aliquet porttitor. Iaculis urna id "
        u"volutpat lacus laoreet non curabitur. Semper quis lectus nulla at "
        u"volutpat diam ut. Enim diam vulputate ut pharetra sit amet aliquam id. "
        u"Etiam dignissim diam quis enim lobortis. Consectetur libero id faucibus "
        u"nisl tincidunt. Et netus et malesuada fames ac turpis egestas. "
        u"Scelerisque mauris pellentesque pulvinar pellentesque habitant morbi "
        u"tristique senectus et. Elementum sagittis vitae et leo duis. Dolor "
        u"purus non enim praesent elementum. At volutpat diam ut venenatis "
        u"tellus. Arcu non odio euismod lacinia at quis. Enim eu turpis egestas "
        u"pretium aenean. Nunc congue nisi vitae suscipit tellus. Rutrum quisque "
        u"non tellus orci ac auctor. Condimentum mattis pellentesque id nibh "
        u"tortor id aliquet lectus proin.</p> "
    )

    now = datetime.now()
    meeting1 = create_meeting(liege, now + relativedelta(months=-1))

    create_item(
        meeting=meeting1,
        representative=liege.representatives_mappings[-1]["representative_key"],
        title=u"Premier point",
        number="1",
        item_type="normal",
        file_names=[u"profiles/demo/data/delibe-1.pdf"],
        category="education",
        deliberation=fake_deliberation,
    )
    meeting2 = create_meeting(liege, now)
    meeting3 = create_meeting(liege, now + relativedelta(months=1))
