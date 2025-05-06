import register from "preact-custom-element";

import CheckboxSelector from "./components/CheckboxSelector";
import AnnexesStatus from "./components/AnnexesStatus";
import InstitutionsSelect from "./components/InstitutionsSelect";
import InstitutionsMap from "./components/InstitutionsMap";
import MasonryColumns from "./components/MasonryColumns";
import DarkModeToggle from "./components/DarkModeToggle";
import LayoutSelect from "./components/LayoutSelect";
import PdfViewer from "./components/PdfViewer";
import MeetingAgenda from "./components/MeetingAgenda";

import "../theme/main.scss";
import Tooltip from "./components/Tooltip";

register(CheckboxSelector, "x-checkbox-selector", ["scope", "checked"]);
register(AnnexesStatus, "x-annexes-status", ["data-annexes"]);
register(InstitutionsSelect, "x-institution-select", ["data-institutions"]);
register(InstitutionsMap, "x-institution-map", []);
register(MasonryColumns, "x-masonry-columns", ["container-selector", "item-selector", "gutter"]);
register(LayoutSelect, "x-layout-select", ["id", "target-selector", "default-option"]);
register(DarkModeToggle, "x-dark-mode-toggle", []);
register(MeetingAgenda, "x-meeting-agenda", ["count", "meeting-url"]);
register(PdfViewer, "x-pdf-viewer", ["file"]);


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
