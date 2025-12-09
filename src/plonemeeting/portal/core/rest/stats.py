# my/package/restapi/fields_usage_stats.py
import random
import logging
from plone.restapi.services import Service
from Products.CMFCore.utils import getToolByName
from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.utils import getAdditionalSchemata
from zope.schema import getFieldsInOrder

logger = logging.getLogger("my.package.fields_usage_stats")


class FieldsUsageStatsGet(Service):
    """JSON stats of how often each field is filled, per content type.
       Supports ?types=..., ?path=/..., ?sample_size=N.
       Correctly counts fields from behaviors/fieldsets by adapting the object.
    """

    def _iter_schemas_for_fti(self, fti, obj=None):
        # Base schema
        base = fti.lookupSchema()
        yield base
        # Behaviors that provide IFormFieldProvider
        # Use context-aware resolution so dynamic behaviors are included
        for sch in getAdditionalSchemata(context=obj, portal_type=fti.id):
            yield sch

    def _value_is_filled(self, value):
        # Treat common “empty” values as not filled
        return value not in (None, "", [], (), {}, set())

    def reply(self):
        portal_catalog = getToolByName(self.context, "portal_catalog")
        portal_types = getToolByName(self.context, "portal_types")

        form = self.request.form

        # ?sample_size=500
        try:
            sample_size = int(form.get("sample_size"))
        except (TypeError, ValueError):
            sample_size = None

        # ?types=Document,News%20Item
        types_param = form.get("types")
        type_ids = [t.strip() for t in types_param.split(",")] if types_param else None

        # ?path=/my/folder
        path = form.get("path") or None
        if path:
            logger.info(f"Filtering catalog query to path: {path}")

        # Collect FTIs
        ftis = [
            fti for fti in portal_types.objectValues()
            if IDexterityFTI.providedBy(fti)
        ]
        if type_ids:
            ftis = [fti for fti in ftis if fti.id in type_ids]

        total_types = len(ftis)
        logger.info(
            f"Starting field usage analysis for {total_types} type(s) "
            f"({'subset' if type_ids else 'all'})"
        )

        results = {}

        for idx, fti in enumerate(ftis, start=1):
            query = {"portal_type": fti.id}
            if path:
                query["path"] = {"query": path}

            brains = portal_catalog(**query)
            total_available = len(brains)
            if total_available == 0:
                logger.info(f"[{idx}/{total_types}] {fti.id}: no items, skipping")
                continue

            # Sampling
            if sample_size and total_available > sample_size:
                brains = random.sample(list(brains), sample_size)
                total = sample_size
                logger.info(
                    f"[{idx}/{total_types}] {fti.id}: sampling {sample_size} of {total_available}"
                )
            else:
                total = total_available
                logger.info(f"[{idx}/{total_types}] {fti.id}: analyzing all {total}")

            # Build the field map ONCE using a representative object when possible,
            # so context-aware behaviors are included.
            # If we can’t get any object, fall back to FTI-only resolution.
            representative_obj = None
            for b in brains:
                try:
                    representative_obj = b.getObject()
                    break
                except Exception:
                    continue

            field_counts = {}  # name -> used count
            schemas = list(self._iter_schemas_for_fti(fti, obj=representative_obj))
            for schema in schemas:
                for name, field in getFieldsInOrder(schema):
                    field_counts.setdefault(name, 0)

            # Iterate items
            processed = 0
            for brain in brains:
                processed += 1
                if processed % 100 == 0:
                    logger.info(f"  {fti.id}: processed {processed}/{total}")
                try:
                    obj = brain.getObject()
                except Exception:
                    logger.warning(f"  Skipping broken brain: {brain.getPath()}")
                    continue

                # Resolve schemas again per object to catch context-enabled behaviors
                obj_schemas = list(self._iter_schemas_for_fti(fti, obj=obj))
                for schema in obj_schemas:
                    # Prefer behavior adapter storage when available
                    storage = schema(obj, None) or obj
                    for name, field in getFieldsInOrder(schema):
                        # Ensure we count fields even if they weren’t in the initial map
                        # (e.g., dynamic behaviors appearing only on some items)
                        if name not in field_counts:
                            field_counts[name] = 0
                        try:
                            value = getattr(storage, name, None)
                        except Exception:
                            value = None
                        if self._value_is_filled(value):
                            field_counts[name] += 1

            # Compile stats
            fields = [
                {
                    "field": name,
                    "used": count,
                    "total": total,
                    "percent": round((count / total) * 100, 1) if total else 0.0,
                }
                for name, count in sorted(field_counts.items())
            ]

            results[fti.id] = {
                "type_id": fti.id,
                "sampled_count": total,
                "path_filtered": bool(path),
                "fields": fields,
            }

            logger.info(f"  Finished {fti.id}")

        logger.info("Field usage analysis completed")

        return {
            "@id": f"{self.context.absolute_url()}/@fields-usage-stats",
            "items_total": len(results),
            "items": list(results.values()),
        }
