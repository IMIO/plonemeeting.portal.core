import $ from "jquery";
import register from "preact-custom-element";

import InstitutionSelect from "./components/InstitutionSelect";
import CheckboxSelector from "./components/CheckboxSelector";
import AnnexesStatus from "./components/AnnexesStatus";
import InstitutionsMap from "./components/InstitutionsMap";
import MasonryColumns from "./components/MasonryColumns";

import "../theme/main.scss";

register(InstitutionSelect, "x-institution-select", ["data-institutions"]);
register(CheckboxSelector, "x-checkbox-selector", ["scope", "checked"]);
register(AnnexesStatus, "x-annexes-status", ["data-annexes"]);
register(InstitutionsMap, "x-institution-map", []);
register(MasonryColumns, "x-masonry-columns", ["container-selector", "item-selector", "gutter"]);

import { i18n } from "@lingui/core";

export const locales = {
    en: "English",
    fr: "French",
};
export const defaultLocale = "en";

i18n.loadLocaleData({
    en: {},
    fr: {},
});

/**
 * We do a dynamic import of just the catalog that we need
 * @param locale any locale string
 */
export async function dynamicActivate(locale) {
    const { messages } = await import(`./locales/${locale}/messages`);
    i18n.load(locale, messages);
    i18n.activate(locale);
}

function setUpEnvironmentLabel() {
    let hostname = document.location.hostname;
    if (hostname === "localhost" || hostname === "0.0.0.0") {
        $("body").append("<span class='environment-label environment-dev'>DEV</span>");
    } else if (hostname.includes("staging")) {
        $("body").append("<span class='environment-label environment-test'>TEST</span>");
    }
}

$(document).ready(function ($) {
    setUpEnvironmentLabel();
    if (window.Faceted) {
        $(Faceted.Events).bind(Faceted.Events.AJAX_QUERY_SUCCESS, function () {
            $(".toggle-link").click(function (e) {
                $("#meeting-custom-info-content-toggle").slideToggle("fast", function () {
                    $(".toggle-link").toggle();
                });
                e.preventDefault();
            });
        });
    }
});
