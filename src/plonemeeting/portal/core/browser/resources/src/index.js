import jquery from "jquery";
import register from "preact-custom-element";

import CheckboxSelector from "./components/CheckboxSelector";
import AnnexesStatus from "./components/AnnexesStatus";
import InstitutionsSelect from "./components/InstitutionsSelect";
import InstitutionsMap from "./components/InstitutionsMap";
import MasonryColumns from "./components/MasonryColumns";
import { StateBadge } from "./components/Badge";

import "../theme/main.scss";

register(CheckboxSelector, "x-checkbox-selector", ["scope", "checked"]);
register(AnnexesStatus, "x-annexes-status", ["data-annexes"]);
register(InstitutionsSelect, "x-institution-select", ["data-institutions"]);
register(InstitutionsMap, "x-institution-map", []);
register(MasonryColumns, "x-masonry-columns", ["container-selector", "item-selector", "gutter"]);
register(StateBadge, "x-state-badge", ["state", "toast"]);

function setUpEnvironmentLabel() {
    let hostname = document.location.hostname;
    if (hostname === "localhost" || hostname === "0.0.0.0") {
        jquery("body").append("<span class='environment-label environment-dev'>DEV</span>");
    } else if (hostname.includes("staging")) {
        jquery("body").append("<span class='environment-label environment-test'>TEST</span>");
    }
}

jquery(document).ready(function ($) {
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
if (module.hot) {
    module.hot.accept();
}

import "preact/debug";
