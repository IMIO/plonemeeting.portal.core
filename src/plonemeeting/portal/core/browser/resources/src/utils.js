export function get_portal_url() {
    return window.PORTAL_URL;
}

export function get_bundle_url() {
    return get_portal_url() + "/++plone++plonemeeting.portal.core";
}
