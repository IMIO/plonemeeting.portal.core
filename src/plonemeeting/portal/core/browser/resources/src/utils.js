export function get_portal_url() {
    return document.body.getAttribute("data-portal-url");
}

export function get_bundle_url() {
    return get_portal_url() + "/++plone++plonemeeting.portal.core";
}

export function randomInt(min, max) {
    const minCeiled = Math.ceil(min);
    const maxFloored = Math.floor(max);
    return Math.floor(Math.random() * (maxFloored - minCeiled) + minCeiled); // The maximum is exclusive and the minimum is inclusive
}
