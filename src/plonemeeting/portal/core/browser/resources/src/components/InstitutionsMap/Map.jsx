import { createContext, h } from "preact";
import { useEffect, useState, useCallback } from "preact/hooks";

import axios from "axios";
import "leaflet/dist/leaflet.css";

import { get_portal_url, get_bundle_url } from "../../utils";
import Legend from "./Legend";
import Mask from "./Mask";
import InstitutionLocation from "./InstitutionLocation";
import { MapContainer, TileLayer, ZoomControl } from "react-leaflet";

/**
 * Display a Leaflet Map with institutions locations
 */
const InstitutionsMap = () => {
    const [institutionLocations, setInstitutionLocations] = useState();
    const [regionBoundaries, setRegionBoundaries] = useState();

    const defaultZoom = window.innerWidth < 900 ? 8 : 9;
    const height = window.innerWidth < 900 ? "500px" : "750px";
    const center = [50.15, 4.55];
    const maxBounds = [
        [54, 10],
        [46, 0],
    ];

    useEffect(() => {
        axios
            .get(get_bundle_url() + "/assets/wallonia-boundaries.json")
            .then((response) => setRegionBoundaries(response.data));
        axios
            .get(get_portal_url() + "/@@institution_locations")
            .then((response) => setInstitutionLocations(response.data));
    }, []);

    return (
        <MapContainer
            center={center}
            maxBounds={maxBounds}
            zoom={defaultZoom}
            minZoom={5}
            maxZoom={13}
            scrollWheelZoom={false}
            zoomControl={false}
            style={{ height: height }}
        >
            <Legend />
            <ZoomControl position={"bottomright"} />
            <TileLayer
                attribution='Carte &copy; <a href="http://osm.org/copyright">OpenStreetMap</a> | Données &copy; <a href="https://www.ngi.be/website/fr/">NGI-IGN</a> '
                url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
            />
            {regionBoundaries && <Mask data={regionBoundaries} />}
            {institutionLocations &&
                Object.keys(institutionLocations).map((key) => (
                    <InstitutionLocation key={key} institution={institutionLocations[key]} />
                ))}
        </MapContainer>
    );
};

export default InstitutionsMap;
