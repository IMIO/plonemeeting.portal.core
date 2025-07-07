from AccessControl import Unauthorized
from Products.Five import BrowserView
from collective.documentgenerator.browser.generation_view import DocumentGenerationView
from collective.documentgenerator.helper import DocumentGenerationHelperView
from imio.helpers.barcode import generate_barcode
from plone import api
from asn1crypto import tsp, cms, x509
from html import escape
from zope.i18n import translate
from plonemeeting.portal.core import _

class PMDocumentGenerationHelperView(DocumentGenerationHelperView):
    """Helper view for document generation."""

    def _load_tst_info(self):
        """
        Return a *tsp.TSTInfo* instance if the timestamp was granted,
        otherwise *None*.
        """
        # 1. Grab raw bytes of the .tsr
        tsr = self.real_context.timestamp
        try:
            data = tsr.data
        except AttributeError:                         # Zope File fallback
            data = tsr.open().read()

        # 2. Decode the outer TimeStampResp
        resp = tsp.TimeStampResp.load(data)
        if resp['status']['status'].native not in ('granted', 'granted_with_mods'):
            return None

        # 3. Walk down into the CMS Time-Stamp Token
        token_ci   = cms.ContentInfo.load(resp['time_stamp_token'].dump())
        signed     = token_ci['content']               # cms.SignedData
        eci        = signed['encap_content_info']      # cms.EncapContentInfo
        content_os = eci['content']                    # OctetString (maybe parsed)

        # 4. If asn1crypto has already parsed the octet-string, use it;
        #    otherwise fall back to manual load from bytes.
        try:
            tst_info = content_os.parsed               # preferred path
        except (ValueError, AttributeError):
            raw = content_os.native
            if not isinstance(raw, (bytes, bytearray)):
                raw = content_os.dump()
            tst_info = tsp.TSTInfo.load(raw)

        return tst_info

    def timestamp_authority(self):
        """ Returns a dict with the TSA authority information."""
        tst = self._load_tst_info()
        if tst is None:
            return {}

        tsa = tst["tsa"]

        # Fallback in case the TSA is not a directory name
        if tsa.name != "directory_name":
            req = getattr(self, "request", None)
            return {
                "general_name": {
                    "label": translate(
                        _(u"label_general_name", default=u"General Name"),
                        context=req,
                    ),
                    "value": str(tsa.chosen.native),
                }
            }

        name: x509.Name = tsa.chosen

        label_map = {
            "common_name":              _(u"label_common_name",
                                          default=u"Common Name"),
            "organization_identifier":  _(u"label_organization_identifier",
                                          default=u"Organization Identifier"),
            "organization_name":        _(u"label_organization_name",
                                          default=u"Organization"),
            "organizational_unit_name": _(u"label_organizational_unit_name",
                                          default=u"Org. Unit"),
            "locality_name":            _(u"label_locality_name",
                                          default=u"Locality"),
            "state_or_province_name":   _(u"label_state_province_name",
                                          default=u"State / Province"),
            "country_name":             _(u"label_country_name",
                                          default=u"Country"),
            "serial_number":            _(u"label_serial_number",
                                          default=u"Serial Number"),
            "email_address":            _(u"label_email_address",
                                          default=u"E-mail"),
            "domain_component":         _(u"label_domain_component",
                                          default=u"Domain"),
        }
        info = {}
        for rdn in name.chosen:
            for ava in rdn:
                oid   = ava["type"].native
                value = ava["value"].native
                label = label_map.get(oid, oid)
                info[oid] = {"label": label, "value": str(value)}

        return info

    def is_timestamped(self):
        """
        True if the .tsr was successfully granted by the TSA
        """
        return self._load_tst_info() is not None

    def timestamp_date(self):
        """
        The actual timestamp generation time (a Python datetime)
        """
        tst = self._load_tst_info()
        return tst['gen_time'].native if tst is not None else None

    def timestamp_precision(self):
        """
        Returns the accuracy of the timestamp in a human-friendly string.

        Examples
        --------
        "1.234 seconds"
        "0.5 seconds"
        "0 seconds (exact)"
        "Not specified"
        """
        tst = self._load_tst_info()
        if tst is None:
            return None

        # -- Pull the optional Accuracy ::= SEQUENCE -------------------------
        try:
            accuracy = tst["accuracy"]  # raises KeyError if absent
        except KeyError:
            return "Not specified"

        if not accuracy or accuracy.native is None:
            return "Not specified"

        acc = accuracy.native  # → plain dict: {'seconds': 1, 'millis': 234, ...}

        seconds = acc.get("seconds", 0) or 0
        millis = acc.get("millis", 0) or 0
        micros = acc.get("micros", 0) or 0

        total_seconds = seconds + millis / 1_000 + micros / 1_000_000

        if total_seconds == 0:
            return "0 seconds (exact)"

        # Decide how many decimals we need
        if micros:
            fmt = "{:.6f}"
        elif millis:
            fmt = "{:.3f}"
        else:
            fmt = "{:.0f}"

        human = fmt.format(total_seconds).rstrip("0").rstrip(".")
        return f"{human} seconde"

    def timestamp_protocol(self):
        """
        The protocol OID used—in RFC 3161, this is
        '1.2.840.113549.1.9.16.1.4'
        """
        return 'RFC 3161'

    def timestamp_hash(self):
        """
        The message imprint digest (hex-encoded)
        """
        tst = self._load_tst_info()
        if tst is None:
            return None
        digest = tst['message_imprint']['hashed_message'].native
        # native is bytes
        return digest.hex()

    def timestamp_algorithm(self):
        """
        The hash algorithm used in the message imprint (e.g. 'sha256')
        """
        tst = self._load_tst_info()
        if tst is None:
            return None
        alg = tst['message_imprint']['hash_algorithm']['algorithm'].native
        return alg

    def qr_code(self, url, scale=2, secure=2):
        """
        Returns a QR code image URL for the timestamp.
        """
        return generate_barcode(
            url,
            barcode=58,
            scale=scale,
            extra_args=f"--secure={secure}",
        )

    def to_html_link(self, url, title=None, klass=""):
        """
        Returns a HTML link URL.
        """
        return f'<a class="{klass}" href="{escape(url)}">{title if title else url}</a>'

    def get_manageable_groups_for_user(self, username):
        """
        Return only 'institution groups' for this user, i.e.,
        groups that match typical institution naming patterns.
        """
        all_user_groups = api.group.get_groups(username=username)
        # We'll say any group ID that ends (or contains) these strings is an 'institution group'
        # Adjust to match your actual naming convention.
        manageable_institution_suffixes = ("decisions_managers", "publications_managers", "managers")
        user_manageable_groups = []
        for group in all_user_groups:
            group_id = group.getId()
            # Keep only groups that are institution-related
            if any(suffix in group_id for suffix in manageable_institution_suffixes):
                user_manageable_groups.append(group)
        return user_manageable_groups
class PMDocumentGenerationView(DocumentGenerationView):
    """Redefine the DocumentGenerationView to extend context available in the template
       and to handle POD templates sent to mailing lists."""

    def __call__(self, template_uid="", output_format="", **kwargs):
        if api.user.is_anonymous():
            raise Unauthorized("You need to be logged in to generate documents.")
        return super().__call__(template_uid, output_format, **kwargs)

    def _get_generation_context(self, helper_view, pod_template):
        """ """
        view = self.context.restrictedTraverse("@@document-generation-helper-view")
        utils_view = self.context.restrictedTraverse("@@utils_view")
        user = api.user.get_current()
        specific_context = {
            "self": self.context,
            "context": self.context,
            "view": view,
            "pod_template": pod_template,
            "utils": utils_view,
            "user": user,
            "portal": api.portal.get(),
            "site_url": api.portal.get().absolute_url(),
        }
        if utils_view.is_in_institution():
            specific_context["institution"] = utils_view.get_current_institution()

        return specific_context
