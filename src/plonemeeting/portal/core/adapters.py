from collective.timestamp.adapters import ITimeStamper
from collective.timestamp.adapters import TimeStamper
from hashlib import md5
from imio.helpers.content import object_values
from io import BytesIO
from plone.namedfile.file import NamedBlobFile
from zope.interface import implementer

import zipfile


@implementer(ITimeStamper)
class PublicationTimeStamper(TimeStamper):
    """Handle timestamping operations on publications"""

    def _member_md5(self, zf: zipfile.ZipFile, name: str, buf_size: int = 128 * 1024) -> str:  # pragma: no cover
        """Return the hex MD5 digest of a file content from a zip file."""
        h = md5()
        with zf.open(name) as fp:
            while chunk := fp.read(buf_size):
                h.update(chunk)
        return h.hexdigest()

    def _zips_equal_by_md5(self, blob_a: bytes, blob_b: bytes) -> bool:  # pragma: no cover
        """
        Two ZIP blobs are considered equal when they contain exactly the same member names,
        and each corresponding member has the same MD5 digest.
        """
        with zipfile.ZipFile(BytesIO(blob_a)) as za, zipfile.ZipFile(BytesIO(blob_b)) as zb:
            names_a = sorted(za.namelist())
            names_b = sorted(zb.namelist())
            if names_a != names_b:
                return False

            digests_a = {n: self._member_md5(za, n) for n in names_a}
            digests_b = {n: self._member_md5(zb, n) for n in names_b}

        return digests_a == digests_b

    def get_data(self):
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_STORED) as zip_file:
            # add main file
            if self.context.file:
                zip_file.writestr(self.context.file.filename, self.context.file.data)
            # add annexes
            for item in object_values(self.context, "File"):
                zip_file.writestr(item.file.filename, item.file.data)
            # add text
            if self.context.text:
                zip_file.writestr("text.txt", self.context.text.raw)
        zip_buffer.seek(0)
        return zip_buffer.getvalue()

    def file_has_changed(self, obj, event):  # pragma: no cover
        """Not used for publications, as we always generate a new timestamp."""
        return not self._zips_equal_by_md5(self.get_data(), obj.timestamped_file.data)

    def _effective_related_indexes(self):
        idxs = super(PublicationTimeStamper, self)._effective_related_indexes()
        # "effective", "effectiveRange", "is_timestamped"
        # already managed by timestamper.timestamp
        idxs.append("year")
        return idxs

    def timestamp(self):
        data, timestamp_date = super(PublicationTimeStamper, self).timestamp()
        formatted_date = timestamp_date.astimezone().strftime("%Y%m%d-%H%M%S")
        filename = f"archive_{formatted_date}.zip"
        self.context.timestamped_file = NamedBlobFile(data=data, filename=filename)
