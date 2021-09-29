from plone.api.portal import set_registry_record
from plone.app.textfield import RichTextValue
from plonemeeting.portal.core.filters.replace_masked_gdpr import ReplaceMaskedGDPR
from plonemeeting.portal.core.tests.portal_test_case import PmPortalDemoFunctionalTestCase


class TestOutputFilters(PmPortalDemoFunctionalTestCase):

    def setUp(self):
        super().setUp()
        self.richtext = u'<p><strong>Article 1er</strong> :</p>' \
                        u'<p>Au scrutin secret et à l’unanimité, de désigner <span class="pm-anonymize"></span>, ' \
                        u'en qualité d’instituteur maternel temporaire mi-temps en remplacement ' \
                        u'de <span class="pm-anonymize"></span> aux écoles communales fondamentales.</p>'

    def test_replace_masked_gdpr(self):
        filter = ReplaceMaskedGDPR(self.institution, None)
        # search for '<span class="pm-anonymize"></span>' (delib_masked_gdpr)
        # to replace with 'TEXTE MASQUÉ | RGPD' and link 'http://nohost/plone/faq/rgpd'
        # (rgpd_masked_text_placeholder + rgpd_masked_text_redirect_path)
        self.assertEqual(filter(self.richtext),
                         u'<p><strong>Article 1er</strong> :</p>'
                         u'<p>Au scrutin secret et à l’unanimité, de désigner '
                         u'<a class="pm-anonymize" href="http://nohost/plone/faq/rgpd"><span>TEXTE MASQUÉ | RGPD</span></a>'
                         u', en qualité d’instituteur maternel temporaire mi-temps en remplacement de '
                         u'<a class="pm-anonymize" href="http://nohost/plone/faq/rgpd"><span>TEXTE MASQUÉ | RGPD</span></a>'
                         u' aux écoles communales fondamentales.</p>'
                         )
        set_registry_record("plonemeeting.portal.core.rgpd_masked_text_redirect_path", "/toto")
        self.assertEqual(filter(self.richtext),
                         u'<p><strong>Article 1er</strong> :</p>'
                         u'<p>Au scrutin secret et à l’unanimité, de désigner '
                         u'<a class="pm-anonymize" href="http://nohost/plone/toto"><span>TEXTE MASQUÉ | RGPD</span></a>'
                         u', en qualité d’instituteur maternel temporaire mi-temps en remplacement de '
                         u'<a class="pm-anonymize" href="http://nohost/plone/toto"><span>TEXTE MASQUÉ | RGPD</span></a>'
                         u' aux écoles communales fondamentales.</p>'
                         )
        self.institution.url_rgpd = "https://www.imio.be/imio-et-vous/rgpd"
        self.assertEqual(filter(self.richtext),
                         u'<p><strong>Article 1er</strong> :</p>'
                         u'<p>Au scrutin secret et à l’unanimité, de désigner '
                         u'<a class="pm-anonymize" href="https://www.imio.be/imio-et-vous/rgpd">'
                         u'<span>TEXTE MASQUÉ | RGPD</span></a>, '
                         u'en qualité d’instituteur maternel temporaire mi-temps en remplacement de '
                         u'<a class="pm-anonymize" href="https://www.imio.be/imio-et-vous/rgpd">'
                         u'<span>TEXTE MASQUÉ | RGPD</span></a> aux écoles communales fondamentales.</p>'
                         )
        set_registry_record("plonemeeting.portal.core.rgpd_masked_text_placeholder", "XXXXXXX")
        self.assertEqual(filter(self.richtext),
                         u'<p><strong>Article 1er</strong> :</p>'
                         u'<p>Au scrutin secret et à l’unanimité, de désigner '
                         u'<a class="pm-anonymize" href="https://www.imio.be/imio-et-vous/rgpd">'
                         u'<span>XXXXXXX</span></a>'
                         u', en qualité d’instituteur maternel temporaire mi-temps en remplacement de '
                         u'<a class="pm-anonymize" href="https://www.imio.be/imio-et-vous/rgpd">'
                         u'<span>XXXXXXX</span></a>'
                         u' aux écoles communales fondamentales.</p>'
                         )
        set_registry_record("plonemeeting.portal.core.delib_masked_gdpr", "YOLO")
        richtext = u'<p><strong>Article 1er</strong> :</p>' \
                   u'<p>Au scrutin secret et à l’unanimité, de désigner YOLO'
        self.assertEqual(filter(richtext),
                         u'<p><strong>Article 1er</strong> :</p>'
                         u'<p>Au scrutin secret et à l’unanimité, de désigner '
                         u'<a class="pm-anonymize" href="https://www.imio.be/imio-et-vous/rgpd">'
                         u'<span>XXXXXXX</span></a>')

    def test_replace_masked_gdpr_applies_on_items_only(self):
        self.item.decision = RichTextValue(raw=self.richtext,
                                           mimeType=u"text/html",
                                           outputMimeType=u"text/x-html-safe",
                                           encoding='utf-8')
        result = u'<p><strong>Article 1er</strong> :</p><p>Au scrutin secret et à l’unanimité, de désigner ' \
                 u'<a class="pm-anonymize" href="http://nohost/plone/faq/rgpd"><span>TEXTE MASQUÉ | RGPD</span></a>, ' \
                 u'en qualité d’instituteur maternel temporaire mi-temps en remplacement de ' \
                 u'<a class="pm-anonymize" href="http://nohost/plone/faq/rgpd"><span>TEXTE MASQUÉ | RGPD</span></a> ' \
                 u'aux écoles communales fondamentales.</p>'
        self.assertEqual(self.item.decision.output_relative_to(self.item), result)
        self.assertTrue(result in self.item())
        self.assertNotEqual(self.item.decision.output_relative_to(self.institution), result)
        self.assertNotEqual(self.item.decision.output_relative_to(self.meeting), result)
