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
    if (hostname === "localhost" || hostname === "0.0.0.0") {
        $("body").append("<span class='environment-label environment-dev'>DEV</span>");
    } else if (hostname.includes("staging")) {
        $("body").append("<span class='environment-label environment-test'>TEST</span>");
    }
}
document.addEventListener("DOMContentLoaded", () => {
    setUpEnvironmentLabel();
});
