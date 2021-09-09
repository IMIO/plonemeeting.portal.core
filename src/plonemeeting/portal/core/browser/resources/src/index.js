import $ from "jquery";
import register from "preact-custom-element";

import InstitutionSelect from "./components/InstitutionSelect";
import CollapsibleCard from "./components/CollapsibleCard";
import InstitutionsCarousel from "./components/InstitutionsCarousel";

import "../theme/main.scss";

register(InstitutionSelect, "x-institution-select", ["data-institutions"]);
register(InstitutionsCarousel, "x-institution-carousel", ["data-institutions"]);
register(CollapsibleCard, "x-collapsible-card", ["data-content"]);


function setUpEnvironmentLabel() {
  let hostname = document.location.hostname;
  if (hostname === "localhost" || hostname === "0.0.0.0") {
    $("body").append("<span class='environment-label environment-dev'>DEV</span>");
  } else if (hostname.includes("staging")) {
    $("body").append("<span class='environment-label environment-test'>TEST</span>");
  }
}

$(document).ready(function($) {
  setUpEnvironmentLabel();
  if (window.Faceted) {
    $(Faceted.Events).bind(Faceted.Events.AJAX_QUERY_SUCCESS, function() {
      $(".toggle-link").click(function(e) {
        $("#meeting-custom-info-content-toggle").slideToggle("fast", function() {
          $(".toggle-link").toggle();
        });
        e.preventDefault();
      });
    });
  }
});
