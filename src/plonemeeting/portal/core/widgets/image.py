from plone.formwidget.namedfile import NamedImageWidget
from plone.formwidget.namedfile.interfaces import INamedImageWidget
from plone.namedfile.interfaces import INamedImageField
from z3c.form.interfaces import IFieldWidget
from z3c.form.interfaces import IFormLayer
from z3c.form.interfaces import IWidget
from z3c.form.widget import FieldWidget
from zope.component import adapter
from zope.interface import implementer
from zope.interface import implementer_only


class IPMNamedImageWidget(INamedImageWidget):
    """Marker interface"""

@implementer_only(IPMNamedImageWidget)
class PMNamedImageWidget(NamedImageWidget):
    """A widget for a named file object"""
    klass = " named-image-widget"

    def download_url(self):
        if (self.field is None) or self.ignoreContext:
            return None
        url_parts = []
        absolute_url_method = getattr(self.context, "absolute_url", None)
        if absolute_url_method:
            # Here is the magic sauce to have the image being displayed in the institution's settings
            url_parts.extend([absolute_url_method(), f"@@images/{self.name.split(".")[-1]}"])
            return "/".join(p for p in url_parts if p)
        else:
            url_parts.append(self.request.getURL())

        url_parts.extend(["++widget++" + self.name, "@@download", self.filename_encoded])

        return "/".join(p for p in url_parts if p)


@implementer(IFieldWidget)
@adapter(IPMNamedImageWidget, IFormLayer)
def PMNamedImageFieldWidget(field, request):
    return FieldWidget(field, PMNamedImageWidget(request))
