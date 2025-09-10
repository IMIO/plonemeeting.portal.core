# -*- coding: utf-8 -*-
"""Installer for the plonemeeting.portal.core package."""

from setuptools import find_packages
from setuptools import setup


long_description = "\n\n".join(
    [
        open("README.rst").read(),
        open("CONTRIBUTORS.rst").read(),
        open("CHANGES.rst").read(),
    ]
)
setup(
    name="plonemeeting.portal.core",
    version="2.2.1",
    description="Plonemeeting decisions publication portal",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    # Get more from https://pypi.org/classifiers/
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: Addon",
        "Framework :: Plone :: 6.1",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
    ],
    keywords="Python Plone",
    author="Laurent Lasudry",
    author_email="laurent.lasudry@affinitic.be",
    url="https://github.com/collective/plonemeeting.portal.core",
    project_urls={
        "PyPI": "https://pypi.python.org/pypi/plonemeeting.portal.core",
        "Source": "https://github.com/collective/plonemeeting.portal.core",
        "Tracker": "https://github.com/collective/plonemeeting.portal.core/issues",
        # 'Documentation': 'https://plonemeeting.portal.core.readthedocs.io/en/latest/',
    },
    license="GPL version 2",
    # packages=find_packages("src", exclude=["ez_setup"]),
    # namespace_packages=["plonemeeting", "plonemeeting.portal"],
    # package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.11",
    install_requires=[
        "setuptools",
        # -*- Extra requirements: -*-
        "collective.fingerpointing",
        "collective.timestamp",
        "collective.autopublishing",
        "collective.documentgenerator>=4.0",
        "collective.excelexport>=2.0",
        "collective.exportimport",
        "collective.z3cform.datagridfield>=3.0.2",
        "eea.facetednavigation>=16.2",
        "plone.api>=2.1.0",
        "plone.app.dexterity",
        "plone.formwidget.hcaptcha>=1.0.3",
        "plone.restapi",
        "requests",
        "z3c.jbot",
        "imio.helpers>=1.0.0rc2",
        "imio.migrator>=1.34",
        "imio.pyutils",
        "rich",
        "shutup",
        "importlib-metadata"
    ],
    extras_require={
        "test": [
            "plone.app.testing",
            # Plone KGS does not use this version, because it would break
            # Remove if your package shall be part of coredev.
            # plone_coredev tests as of 2016-04-01.
            "plone.testing>=5.0.0",
            "plone.app.contenttypes",
            "plone.app.robotframework[test]",
            "mockito"
        ]
    },
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    [console_scripts]
    update_locale = plonemeeting.portal.core.locales.update:update_locale
    """,
)
