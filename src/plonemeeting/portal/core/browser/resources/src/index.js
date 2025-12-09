import register from "preact-custom-element";
import loadable from '@loadable/component'

import CheckboxSelector from "./components/CheckboxSelector";
import AnnexesStatus from "./components/AnnexesStatus";
import InstitutionsSelect from "./components/InstitutionsSelect";
import MasonryColumns from "./components/MasonryColumns";
import DarkModeToggle from "./components/DarkModeToggle";
import LayoutSelect from "./components/LayoutSelect";
import MeetingAgenda from "./components/MeetingAgenda";
import Tooltip from "./components/Tooltip";
import TableOfContent from "./components/TableOfContent";
// import ContentBrowser from "./components/ContentBrowser/App";

import registry from "@patternslib/patternslib/src/core/registry";


// Loadable components, for code-splitting and lazy loading
const TimestampCheck = loadable(() => import('./components/TimestampCheck'))
const PdfViewer = loadable(() => import('./components/PdfViewer'));

const InstitutionsMap = loadable(() => import('./components/InstitutionsMap'));
import "../theme/main.scss";

register(CheckboxSelector, "x-checkbox-selector", ["scope", "checked"]);
register(AnnexesStatus, "x-annexes-status", ["data-annexes"]);
register(InstitutionsSelect, "x-institution-select", ["data-institutions"]);
register(MasonryColumns, "x-masonry-columns", ["container-selector", "item-selector", "gutter"]);
register(LayoutSelect, "x-layout-select", ["id", "target-selector", "default-option"]);
register(DarkModeToggle, "x-dark-mode-toggle", []);
register(MeetingAgenda, "x-meeting-agenda", ["count", "meeting-url"]);
register(InstitutionsMap, "x-institution-map", []);
register(PdfViewer, "x-pdf-viewer", ["file"]);
register(TimestampCheck, "x-timestamp-check", []);
register(TableOfContent, "x-table-of-content", []);


function setUpEnvironmentLabel() {
  let hostname = document.location.hostname;
  let body = document.querySelector("body");
  let span = document.createElement("span");
  if (hostname === "localhost" || hostname === "0.0.0.0") {
    span.className = 'environment-label environment-dev';
    span.textContent = 'DEV';
  } else if (hostname.includes("staging")) {
    span.className = 'environment-label environment-test';
    span.textContent = 'STAGING';
  } else if (hostname.includes("test")) {
    span.className = 'environment-label environment-test';
    span.textContent = 'TEST';
  }
  body.appendChild(span);
}

function displayInSettingsPath() {
  let settingsTab = document.body.querySelector(".institution_settings");
  if (settingsTab && document.body.className.includes("portaltype-institution")) {
    settingsTab.className = settingsTab.className + " current inPath"
  }
}

document.addEventListener("DOMContentLoaded", () => {
  setUpEnvironmentLabel();
  displayInSettingsPath();
  // As the tooltip accepts slots we need to use shadow dom and register it after DOMContentLoaded
  register(Tooltip, "x-tooltip", ["target-selector", "position"], {shadow: false});
});


// document.addEventListener('DOMContentLoaded', function () {
//   function markTabsWithErrors() {
//     const tabLinks = document.querySelectorAll('.autotoc-nav a');
//     const errors = [];
//
//     tabLinks.forEach(function (tabLink, index) {
//       const fieldsets = document.querySelectorAll('fieldset.autotoc-section');
//       const fieldset = fieldsets[index];
//
//       if (fieldset) {
//         const errorFields = fieldset.querySelectorAll('.error, .is-invalid, .has-error');
//
//         if (errorFields.length > 0 && !tabLink.classList.contains('has-tab-error')) {
//           tabLink.classList.add('has-tab-error');
//         } else if (errorFields.length === 0 && tabLink.classList.contains('has-tab-error')) {
//           tabLink.classList.remove('has-tab-error');
//         }
//
//         // Collect error details
//         if (errorFields.length > 0) {
//           const tabName = tabLink.textContent.trim();
//
//           errorFields.forEach(function (errorField) {
//             // Get the field label
//             const label = errorField.querySelector('label.form-label');
//             const fieldName = label ? label.textContent.trim() : 'Champ indéterminé';
//
//             // Get the error message
//             const errorMessage = errorField.querySelector('.invalid-feedback');
//             const message = errorMessage ? errorMessage.textContent.trim() : 'Erreur de validation';
//
//             errors.push({
//               tab: tabName,
//               tabLink: tabLink,
//               field: fieldName,
//               message: message
//             });
//           });
//         }
//       }
//     });
//
//     // Update portal message
//     updatePortalMessage(errors);
//   }
//
//   function updatePortalMessage(errors) {
//     const portalMessage = document.querySelector('.portalMessage.statusmessage-error');
//
//     if (!portalMessage) return;
//
//     // Find or create the error list container
//     let errorListContainer = portalMessage.querySelector('.error-list-container');
//
//     if (errors.length === 0) {
//       if (errorListContainer) {
//         errorListContainer.remove();
//       }
//       return;
//     }
//
//     if (!errorListContainer) {
//       errorListContainer = document.createElement('div');
//       errorListContainer.className = 'error-list-container';
//       portalMessage.appendChild(errorListContainer);
//     }
//
//     // Build the error list HTML
//     let html = '<ul class="error-list list-group list-group-flush mb-0 mt-2">';
//
//     errors.forEach(function (error) {
//       html += `<li class="list-group-item list-group-item-danger">
//                 <a href="#" class="error-link" data-tab-id="${error.tabLink.id}">
//                     <i class="bi bi-chevron-double-right"></i>
//                     <strong>${error.tab} / ${error.field}</strong>
//                 </a>
//                 <small>${error.message}</small>
//             </li>`;
//     });
//
//     html += '</ul>';
//     errorListContainer.innerHTML = html;
//
//     // Add click handlers to navigate to the error
//     errorListContainer.querySelectorAll('.error-link').forEach(function (link) {
//       link.addEventListener('click', function (e) {
//         e.preventDefault();
//         const tabId = this.getAttribute('data-tab-id');
//         const tab = document.getElementById(tabId);
//         if (tab) {
//           tab.click();
//         }
//       });
//     });
//   }
//
//   // Run on page load
//   markTabsWithErrors();
//
//   // Observe for dynamic changes
//   const form = document.getElementById('form');
//   if (form) {
//     const observer = new MutationObserver(function (mutations) {
//       const relevantChange = mutations.some(function (mutation) {
//         return !mutation.target.closest('.autotoc-nav') &&
//           !mutation.target.closest('.portalMessage');
//       });
//
//       if (relevantChange) {
//         markTabsWithErrors();
//       }
//     });
//
//     observer.observe(form, {
//       childList: true,
//       subtree: true,
//       attributes: true,
//       attributeFilter: ['class']
//     });
//   }
// });
document.addEventListener('DOMContentLoaded', function () {
  let scrollPreventionTimeout = null;

  // Prevent scrolling function
  function preventScrolling() {
    // Clear any existing timeout
    if (scrollPreventionTimeout) {
      clearTimeout(scrollPreventionTimeout);
    }

    // Store current scroll position
    const scrollY = window.scrollY;
    const scrollX = window.scrollX;

    // Prevent scrolling
    document.body.style.overflow = 'hidden';
    document.documentElement.style.overflow = 'hidden';

    // Restore scroll position if it changes
    const restoreScroll = function() {
      window.scrollTo(scrollX, scrollY);
    };

    window.addEventListener('scroll', restoreScroll);

    // Re-enable scrolling after 1 second because not sure what causes the page to be scrolled to the bottom instantly
    scrollPreventionTimeout = setTimeout(function() {
      document.body.style.overflow = '';
      document.documentElement.style.overflow = '';
      window.removeEventListener('scroll', restoreScroll);
    }, 1000);
  }

  function markTabsWithErrors() {
    const tabLinks = document.querySelectorAll('.autotoc-nav a');
    const errors = [];

    tabLinks.forEach(function (tabLink, index) {
      const fieldsets = document.querySelectorAll('fieldset.autotoc-section');
      const fieldset = fieldsets[index];

      if (fieldset) {
        const errorFields = fieldset.querySelectorAll('.error, .is-invalid, .has-error');

        if (errorFields.length > 0 && !tabLink.classList.contains('has-tab-error')) {
          tabLink.classList.add('has-tab-error');
        } else if (errorFields.length === 0 && tabLink.classList.contains('has-tab-error')) {
          tabLink.classList.remove('has-tab-error');
        }

        // Collect error details
        if (errorFields.length > 0) {
          const tabName = tabLink.textContent.trim();

          errorFields.forEach(function (errorField) {
            // Get the field label
            const label = errorField.querySelector('label.form-label');
            const fieldName = label ? label.textContent.trim() : 'Champ indéterminé';

            // Get the error message
            const errorMessage = errorField.querySelector('.invalid-feedback');
            const message = errorMessage ? errorMessage.textContent.trim() : 'Erreur de validation';

            errors.push({
              tab: tabName,
              tabLink: tabLink,
              field: fieldName,
              message: message
            });
          });
        }
      }
    });

    // Update portal message
    updatePortalMessage(errors);
  }

  function updatePortalMessage(errors) {
    const portalMessage = document.querySelector('.portalMessage.statusmessage-error');

    if (!portalMessage) return;

    // Find or create the error list container
    let errorListContainer = portalMessage.querySelector('.error-list-container');

    if (errors.length === 0) {
      if (errorListContainer) {
        errorListContainer.remove();
      }
      return;
    }

    const isNewErrorList = !errorListContainer;

    if (!errorListContainer) {
      errorListContainer = document.createElement('div');
      errorListContainer.className = 'error-list-container';
      portalMessage.appendChild(errorListContainer);
    }

    // Build the error list HTML
    let html = '<ul class="error-list list-group list-group-flush mb-0 mt-2">';

    errors.forEach(function (error) {
      html += `<li class="list-group-item list-group-item-danger">
                <a href="#" class="error-link" data-tab-id="${error.tabLink.id}">
                    <i class="bi bi-chevron-double-right"></i>
                    <strong>${error.tab} / ${error.field}</strong>
                </a>
                <small>${error.message}</small>
            </li>`;
    });

    html += '</ul>';
    errorListContainer.innerHTML = html;

    // Add click handlers to navigate to the error
    errorListContainer.querySelectorAll('.error-link').forEach(function (link) {
      link.addEventListener('click', function (e) {
        e.preventDefault();
        const tabId = this.getAttribute('data-tab-id');
        const tab = document.getElementById(tabId);
        if (tab) {
          tab.click();
        }
      });
    });

    // Prevent scrolling if this is a new error list being displayed
    if (isNewErrorList && errors.length > 0) {
      preventScrolling();
    }
  }

  // Run on page load
  markTabsWithErrors();

  // Observe for dynamic changes
  const form = document.getElementById('form');
  if (form) {
    const observer = new MutationObserver(function (mutations) {
      const relevantChange = mutations.some(function (mutation) {
        return !mutation.target.closest('.autotoc-nav') &&
          !mutation.target.closest('.portalMessage');
      });

      if (relevantChange) {
        markTabsWithErrors();
      }
    });

    observer.observe(form, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['class']
    });
  }
});
