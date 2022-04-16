import $ from "jquery";
import register from "preact-custom-element";

import InstitutionsSelect from "./components/InstitutionsSelect";
import InstitutionsMap from "./components/InstitutionsMap";
import MasonryColumns from "./components/MasonryColumns";

import "../theme/main.scss";
import "preact/debug";

register(InstitutionsSelect, "x-institution-select", ["data-institutions"]);
register(InstitutionsMap, "x-institution-map", []);
register(MasonryColumns, "x-masonry-columns", ["container-selector", "item-selector", "gutter"]);

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
