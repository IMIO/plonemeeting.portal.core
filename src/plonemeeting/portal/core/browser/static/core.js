jQuery(document).ready(function ($) {
  if (window.Faceted) {
    jQuery(Faceted.Events).bind(Faceted.Events.AJAX_QUERY_SUCCESS, function () {
      $(".toggle-link").click(function (e) {
        $("#meeting-custom-info-content-toggle").slideToggle("fast", function () {
          $(".toggle-link").toggle();
        });
        e.preventDefault();
      });
    });
  }
});
