from plone.api.portal import set_registry_record
from plonemeeting.portal.core.filters.replace_masked_gdpr import ReplaceMaskedGDPR
from plonemeeting.portal.core.tests.portal_test_case import PmPortalDemoFunctionalTestCase


class TestOutputFilters(PmPortalDemoFunctionalTestCase):

    def test_replace_masked_gdpr(self):
        filter = ReplaceMaskedGDPR(self.institution, None)
        # search for '<span class="pm-anonymize"></span>' (delib_masked_gdpr)
        # to replace with '[Texte masqué RGPD]' and link 'http://nohost/plone#rgpd'
        # (rgpd_masked_text_placeholder + rgpd_masked_text_redirect_path)
        richtext = '<p><strong>Article 1er</strong> :</p>' \
                   '<p>Au scrutin secret et à l’unanimité, de désigner <span class="pm-anonymize"></span>, ' \
                   'en qualité d’instituteur maternel temporaire mi-temps en remplacement ' \
                   'de <span class="pm-anonymize"></span> aux écoles communales fondamentales.</p>'

        self.assertEqual(filter(richtext),
                         '<p><strong>Article 1er</strong> :</p>'
                         '<p>Au scrutin secret et à l’unanimité, de désigner '
                         '<a class="pm-anonymize" href="http://nohost/plone#rgpd"><span>[Texte masqué RGPD]</span></a>'
                         ', en qualité d’instituteur maternel temporaire mi-temps en remplacement de '
                         '<a class="pm-anonymize" href="http://nohost/plone#rgpd"><span>[Texte masqué RGPD]</span></a> '
                         'aux écoles communales fondamentales.</p>'
                         )
        set_registry_record("plonemeeting.portal.core.rgpd_masked_text_redirect_path", "/toto")
        self.assertEqual(filter(richtext),
                         '<p><strong>Article 1er</strong> :</p>'
                         '<p>Au scrutin secret et à l’unanimité, de désigner '
                         '<a class="pm-anonymize" href="http://nohost/plone/toto"><span>[Texte masqué RGPD]</span></a>'
                         ', en qualité d’instituteur maternel temporaire mi-temps en remplacement de '
                         '<a class="pm-anonymize" href="http://nohost/plone/toto"><span>[Texte masqué RGPD]</span></a> '
                         'aux écoles communales fondamentales.</p>'
                         )
        self.institution.url_rgpd = "https://www.imio.be/imio-et-vous/rgpd"
        self.assertEqual(filter(richtext),
                         '<p><strong>Article 1er</strong> :</p>'
                         '<p>Au scrutin secret et à l’unanimité, de désigner '
                         '<a class="pm-anonymize" href="https://www.imio.be/imio-et-vous/rgpd">'
                         '<span>[Texte masqué RGPD]</span></a>, '
                         'en qualité d’instituteur maternel temporaire mi-temps en remplacement de '
                         '<a class="pm-anonymize" href="https://www.imio.be/imio-et-vous/rgpd">'
                         '<span>[Texte masqué RGPD]</span></a> aux écoles communales fondamentales.</p>'
                         )
        set_registry_record("plonemeeting.portal.core.rgpd_masked_text_placeholder", "XXXXXXX")
        self.assertEqual(filter(richtext),
                         '<p><strong>Article 1er</strong> :</p>'
                         '<p>Au scrutin secret et à l’unanimité, de désigner '
                         '<a class="pm-anonymize" href="https://www.imio.be/imio-et-vous/rgpd"><span>XXXXXXX</span></a>'
                         ', en qualité d’instituteur maternel temporaire mi-temps en remplacement de '
                         '<a class="pm-anonymize" href="https://www.imio.be/imio-et-vous/rgpd"><span>XXXXXXX</span></a>'
                         ' aux écoles communales fondamentales.</p>'
                         )
        set_registry_record("plonemeeting.portal.core.delib_masked_gdpr", "YOLO")
        richtext = '<p><strong>Article 1er</strong> :</p>' \
                   '<p>Au scrutin secret et à l’unanimité, de désigner YOLO'
        self.assertEqual(filter(richtext),
                         '<p><strong>Article 1er</strong> :</p>'
                         '<p>Au scrutin secret et à l’unanimité, de désigner '
                         '<a class="pm-anonymize" href="https://www.imio.be/imio-et-vous/rgpd">'
                         '<span>XXXXXXX</span></a>')
