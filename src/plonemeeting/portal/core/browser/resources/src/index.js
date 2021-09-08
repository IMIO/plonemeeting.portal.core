import $ from "jquery";
import "../theme/main.scss";

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
