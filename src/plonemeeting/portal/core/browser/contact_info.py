# -*- coding: utf-8 -*-
from Acquisition import aq_inner
from plone.autoform import directives
from plone.formwidget.hcaptcha import HCaptchaFieldWidget
from plonemeeting.portal.core import _
from Products.CMFPlone.browser.contact_info import ContactForm
from Products.CMFPlone.browser.interfaces import IContactForm
from Products.statusmessages.interfaces import IStatusMessage
from z3c.form import button
from zope import schema
from zope.component import getMultiAdapter


class ICaptchaContactForm(IContactForm):

    directives.widget("captcha", HCaptchaFieldWidget)
    captcha = schema.TextLine(title=_("Verification"), description="", required=False)


class CaptchaContactForm(ContactForm):
    schema = ICaptchaContactForm

    @button.buttonAndHandler(_("label_send", default="Send"), name="send")
    def handle_send(self, action):
        captcha = getMultiAdapter(
            (aq_inner(self.context), self.request), name="hcaptcha"
        )
        if captcha.verify():
            return ContactForm.handle_send(self, action)
        else:
            IStatusMessage(self.request).add(
                _(
                    "The CAPTCHA validation was unsuccessful. "
                    "Please retry by carefully following the instructions."
                ),
                type="error",
            )
