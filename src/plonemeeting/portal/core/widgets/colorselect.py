# -*- coding: utf-8 -*-
from z3c.form.browser import widget
from z3c.form.browser.text import TextWidget
from z3c.form.browser.widget import HTMLTextInputWidget
from z3c.form.interfaces import IFieldWidget
from z3c.form.interfaces import IFormLayer
from z3c.form.interfaces import IWidget
from z3c.form.widget import FieldWidget
from z3c.form.widget import Widget
from zope.component import adapter
from zope.interface import implementer
from zope.interface import implementer_only
from zope.schema.interfaces import IField


class IColorSelectWidget(IWidget):
    """Marker interface"""

@implementer_only(IColorSelectWidget)
class ColorSelectWidget(TextWidget):
    """
    Color selector widget which use the native color selector from the browser
    """

    klass = "color-select-widget"
    css = u'color'

@adapter(IField, IFormLayer)
@implementer(IFieldWidget)
def ColorSelectFieldWidget(field, request):
    return FieldWidget(field, ColorSelectWidget(request))
