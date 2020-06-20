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

function update_colors() {
  // Update global css color variables based on what colorsViewlet
  let root = document.documentElement;
  root.style.setProperty('--main-nav-color', portalColors.mainNavColor);
  root.style.setProperty('--main-nav-text-color', portalColors.mainNavTextColor);
}

update_colors();


