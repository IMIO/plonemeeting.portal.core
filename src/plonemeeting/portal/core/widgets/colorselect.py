# -*- coding: utf-8 -*-
from z3c.form.interfaces import IFormLayer
from z3c.form.interfaces import IFieldWidget

from z3c.form.interfaces import IWidget
from z3c.form.widget import FieldWidget
from z3c.form.browser.text import TextWidget
from zope.component import adapter
from zope.interface import implementer
from zope.interface import implementer_only
from zope.schema.interfaces import IField


class IColorSelectWidget(IWidget):
    """Marker interface"""


class ColorSelectWidget(TextWidget):
    """
    Color selector widget which use the native color selector from the browser
    """
    implementer_only(IColorSelectWidget)
    klass = "color-select-widget"


@adapter(IField, IFormLayer)
@implementer(IFieldWidget)
def ColorSelectFieldWidget(field, request):
    return FieldWidget(field, ColorSelectWidget(request))
