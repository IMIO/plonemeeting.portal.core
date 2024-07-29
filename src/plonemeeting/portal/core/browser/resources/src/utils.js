export function get_portal_url() {
    return document.body.getAttribute("data-portal-url");
}

export function get_bundle_url() {
    return get_portal_url() + "/++plone++plonemeeting.portal.core";
}
