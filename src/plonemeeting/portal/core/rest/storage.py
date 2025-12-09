from Products.CMFCore.utils import getToolByName
import sys
import pickle
import logging
from ZODB.blob import Blob
from plone.namedfile.interfaces import INamed
from plone.restapi.services import Service

logger = logging.getLogger("my.package.restapi.base_stats")


class BaseContentStatsService:
    """Common logic shared by content stats services (DB size, counts, etc.)"""

    def _parse_params(self):
        """Parse shared query parameters (path, depth, sort, order)."""
        form = self.request.form

        # ?path=/Plone/news
        root_path = form.get("path")
        if root_path:
            logger.info(f"Restricting stats to subtree {root_path}")

        # ?depth=2
        try:
            depth = int(form.get("depth", 1))
        except ValueError:
            depth = 1

        # ?sort=size|id (default: size)
        sort_by = form.get("sort", "size").lower()
        if sort_by not in ("size", "id"):
            sort_by = "size"

        # ?order=asc|desc
        order = form.get("order", None)
        if order not in ("asc", "desc"):
            order = "desc" if sort_by == "size" else "asc"

        return root_path, depth, sort_by, order

    def _collect_brains(self, root_path):
        """Query the catalog for objects under root_path (or entire site)."""
        catalog = getToolByName(self.context, "portal_catalog")
        query = {}
        if root_path:
            query["path"] = {"query": root_path}
        brains = catalog(**query)
        logger.info(f"Collected {len(brains)} brains for stats computation")
        return brains

    def _group_key(self, brain, depth):
        """Compute the grouping path key given a brain and depth."""
        parts = brain.getPath().strip("/").split("/")
        if len(parts) >= depth:
            return "/" + "/".join(parts[:depth])
        return "/" + "/".join(parts)


def estimate_obj_size(obj):
    """Return (pickle_bytes, blob_bytes) for one ZODB object."""
    pickle_bytes = 0
    blob_bytes = 0

    # Pickle payload size (approx ZODB record)
    try:
        state = obj._p_marshal_state() if hasattr(obj, "_p_marshal_state") else obj
        pickle_bytes += len(pickle.dumps(state))
    except Exception:
        try:
            pickle_bytes += len(pickle.dumps(obj))
        except Exception:
            pickle_bytes += sys.getsizeof(obj)

    # Blob / file field sizes
    try:
        for name in dir(obj):
            if name.startswith("_"):
                continue
            try:
                val = getattr(obj, name)
            except Exception:
                continue
            if INamed.providedBy(val) and getattr(val, "data", None):
                blob_bytes += len(val.data)
            elif isinstance(val, Blob):
                try:
                    blob_bytes += val.size
                except Exception:
                    pass
    except Exception:
        pass

    return pickle_bytes, blob_bytes


class DBSizeStatsGet(Service, BaseContentStatsService):
    """Return JSON with approximate DB pickle/blob size per path."""

    def reply(self):
        root_path, depth, sort_by, order = self._parse_params()
        brains = self._collect_brains(root_path)
        reverse = (order == "desc")

        groups = {}

        for i, brain in enumerate(brains, start=1):
            if i % 500 == 0:
                logger.info(f"Processed {i}/{len(brains)} brains...")

            try:
                obj = brain.getObject()
            except Exception:
                continue

            key = self._group_key(brain, depth)
            pickle_b, blob_b = estimate_obj_size(obj)

            grp = groups.setdefault(key, {"count": 0, "pickle_bytes": 0, "blob_bytes": 0})
            grp["count"] += 1
            grp["pickle_bytes"] += pickle_b
            grp["blob_bytes"] += blob_b

        # Sort
        if sort_by == "id":
            sorted_items = sorted(groups.items(), key=lambda kv: kv[0].lower(), reverse=reverse)
        else:
            sorted_items = sorted(
                groups.items(),
                key=lambda kv: kv[1]["pickle_bytes"] + kv[1]["blob_bytes"],
                reverse=reverse,
            )

        # Build output
        results = []
        for path, data in sorted_items:
            total_bytes = data["pickle_bytes"] + data["blob_bytes"]
            results.append(
                {
                    "path": path,
                    "count": data["count"],
                    "pickle_bytes": data["pickle_bytes"],
                    "blob_bytes": data["blob_bytes"],
                    "total_bytes": total_bytes,
                    "pickle_mb": round(data["pickle_bytes"] / (1024 * 1024), 2),
                    "blob_mb": round(data["blob_bytes"] / (1024 * 1024), 2),
                    "total_mb": round(total_bytes / (1024 * 1024), 2),
                }
            )

        total_pickle = sum(d["pickle_bytes"] for d in groups.values())
        total_blob = sum(d["blob_bytes"] for d in groups.values())
        total_bytes = total_pickle + total_blob

        return {
            "@id": f"{self.context.absolute_url()}/@db-size-stats",
            "depth": depth,
            "sort": sort_by,
            "order": order,
            "items_total": len(results),
            "totals": {
                "pickle_bytes": total_pickle,
                "blob_bytes": total_blob,
                "total_bytes": total_bytes,
                "pickle_mb": round(total_pickle / (1024 * 1024), 2),
                "blob_mb": round(total_blob / (1024 * 1024), 2),
                "total_mb": round(total_bytes / (1024 * 1024), 2),
            },
            "items": results,
        }


class ContentCountStatsGet(Service, BaseContentStatsService):
    """Return JSON with counts of objects per path."""

    def reply(self):
        root_path, depth, sort_by, order = self._parse_params()
        brains = self._collect_brains(root_path)
        reverse = (order == "desc")

        groups = {}

        for i, brain in enumerate(brains, start=1):
            if i % 500 == 0:
                logger.info(f"Processed {i}/{len(brains)} brains...")

            key = self._group_key(brain, depth)
            groups[key] = groups.get(key, 0) + 1

        # Sort
        if sort_by == "id":
            sorted_items = sorted(groups.items(), key=lambda kv: kv[0].lower(), reverse=reverse)
        else:  # sort_by == "size"
            sorted_items = sorted(groups.items(), key=lambda kv: kv[1], reverse=reverse)

        # Build output
        results = [
            {"path": path, "count": count}
            for path, count in sorted_items
        ]

        total = sum(groups.values())

        return {
            "@id": f"{self.context.absolute_url()}/@content-count-stats",
            "depth": depth,
            "sort": sort_by,
            "order": order,
            "items_total": len(results),
            "total_objects": total,
            "items": results,
        }
