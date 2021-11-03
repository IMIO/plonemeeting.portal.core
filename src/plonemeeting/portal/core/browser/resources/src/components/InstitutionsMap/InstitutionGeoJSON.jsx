import { h } from "preact";
import { GeoJSON } from "react-leaflet";
import { useContext, useState } from "preact/hooks";
import { useMemo } from "preact/compat";

/**
 * A map legend for institutions map
 */
const InstitutionGeoJSON = ({ children, geoShape, state, selected, onClick }) => {
    const defaultPathOption = { weight: 1.5, color: "#DE007B", fillOpacity: 0.1 };
    const selectedPathOption = { weight: 1.5, color: "#DE007B", fillOpacity: 0.8 };

    const inProgressPathOption = { weight: 1.5, color: "#808080", fillOpacity: 0.1 };
    const selectedInProgressPathOption = {
        weight: 1.5,
        color: "#808080",
        fillOpacity: 0.8,
    };
    const getPathOptionForInstitution = () => {
        if (selected) {
            if (state === "private") {
                return selectedInProgressPathOption;
            } else {
                return selectedPathOption;
            }
        } else {
            if (state === "published") {
                return defaultPathOption;
            } else {
                return inProgressPathOption;
            }
        }
    };

    return (
        <GeoJSON
            eventHandlers={{
                click: onClick,
            }}
            pathOptions={getPathOptionForInstitution()}
            data={geoShape}
        >
            {children}
        </GeoJSON>
    );
};

export default InstitutionGeoJSON;
