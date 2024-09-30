from collective.timestamp.adapters import ITimeStamper
from collective.timestamp.adapters import TimeStamper
from imio.helpers.content import object_values
from io import BytesIO
from plone.namedfile.file import NamedBlobFile
from zope.interface import implementer

import zipfile


@implementer(ITimeStamper)
class PublicationTimeStamper(TimeStamper):
    """Handle timestamping operations on publications"""

    def get_data(self):
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
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

    def file_has_changed(self, obj, event):
        return obj.timestamped_file.data != self.get_data()

    def _effective_related_indexes(self):
        idxs = super(PublicationTimeStamper, self)._effective_related_indexes()
        # "effective", "effectiveRange", "is_timestamped"
        # already managed by timestamper.timestamp
        idxs.append("year")
        return idxs

    def timestamp(self):
        data, timestamp = super(PublicationTimeStamper, self).timestamp()
        formatted_date = (
            timestamp["timestamp_date"].astimezone().strftime("%Y%m%d-%H%M%S")
        )
        filename = f"archive_{formatted_date}.zip"
        self.context.timestamped_file = NamedBlobFile(data=data, filename=filename)
