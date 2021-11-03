import { h } from "preact";
import CircleChevronRight from "../../../assets/circle-chevron-right.svg";
import { GeoJSON, Popup, useMap } from "react-leaflet";
import { useEffect, useRef, useState } from "preact/hooks";
import { useMemo } from "preact/compat";
import InstitutionGeoJSON from "./InstitutionGeoJSON";
import InstitutionPopup from "./InstitutionPopup";

/**
 * A map legend for institutions map
 */
const InstitutionLocation = ({ institution }) => {
    const [isSelected, setIsSelected] = useState(false);

    return (
        <InstitutionGeoJSON
            state={institution["state"]}
            geoShape={institution["data"]["fields"]["geo_shape"]}
            institutionId={institution}
            selected={isSelected}
            onClick={() => setIsSelected(true)}
        >
            <InstitutionPopup institution={institution} onClose={() => setIsSelected(false)} />
        </InstitutionGeoJSON>
    );
};

export default InstitutionLocation;
