# -*- coding: utf-8 -*-

from imio.migrator.migrator import Migrator

import logging


logger = logging.getLogger("plonemeeting.portal.core")


class MigrateTo1006(Migrator):

    def _transform_delib_categories_to_dict(self):
        logger.info("Transforming delib_categories to proper dict...")
        brains = self.catalog(portal_type="Institution")
        for brain in brains:
            institution = brain.getObject()
            cat_dict = {}
            if hasattr(institution, "delib_categories") and institution.delib_categories:
                cat_dict = {}
                for category_id, category_title in institution.delib_categories:
                    cat_dict[category_id] = category_title
            institution.delib_categories = cat_dict

    def _transform_text_url_param_to_datagrid(self):
        def url_to_dict(url, include=None, exclude=[]):
            res = []
            for splitted in url.split('&'):
                if splitted:
                    sub = splitted.split('=')
                    parameter = sub[0].strip()
                    if (not include or parameter in include) and parameter not in exclude:
                        res.append(
                            {
                                'parameter': parameter,
                                # special behavior for fullobjects parameter
                                # that does not have a value
                                'value': len(sub) > 1 and sub[1].strip() or "true"
                            }
                        )
            return res

        logger.info("Transforming TextLine query parameter to datagridfields...")
        brains = self.catalog(portal_type="Institution")
        for brain in brains:
            institution = brain.getObject()
            if hasattr(institution, "additional_meeting_query_string_for_list"):
                if institution.additional_meeting_query_string_for_list is not None:
                    institution.meeting_filter_query = url_to_dict(institution.additional_meeting_query_string_for_list)
                delattr(institution, "additional_meeting_query_string_for_list")

            if hasattr(institution, "additional_published_items_query_string"):
                if institution.additional_published_items_query_string is not None:
                    institution.item_filter_query = url_to_dict(
                        institution.additional_published_items_query_string,
                        include=['review_state', 'listType'])
                    institution.item_content_query = url_to_dict(
                        institution.additional_published_items_query_string,
                        exclude=['review_state', 'listType'])
                delattr(institution, "additional_published_items_query_string")

        logger.info("Done.")

    def run(self):
        logger.info("Migrating to plonemeeting.portal.core 1006...")
        self._transform_delib_categories_to_dict()
        self._transform_text_url_param_to_datagrid()


def migrate(context):
    """
    This migration function will:
       1) migrate delib_categories to proper dict
       2) change TextLine query parameter to datagridfields :
          - additional_meeting_query_string_for_list
          - additional_published_items_query_string
    """
    migrator = MigrateTo1006(context)
    migrator.run()
    migrator.finish()
