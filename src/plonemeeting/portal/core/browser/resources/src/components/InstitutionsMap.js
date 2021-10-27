import { Fragment, h, render } from "preact";
import { useEffect, useState, useCallback } from "preact/hooks";
import loadable from "@loadable/component";
import axios from "axios";
import "leaflet/dist/leaflet.css";

import CircleChevronRight from "../../assets/circle-chevron-right.svg";
import { get_bundle_url, get_portal_url } from "../utils";
import { Mask } from "./LeafletMask";

const ReactLeaflet = loadable.lib(() => import("react-leaflet"));

/**
 * Display a Leaflet Map with institutions geoJSON locations
 * TODO: Split this in multiple sub-components
 */
const InstitutionsMap = (props) => {
    const [institutionLocations, setInstitutionLocations] = useState();
    const [regionBoundaries, setRegionBoundaries] = useState();
    const [selectedInstitutionId, setSelectedInstitutionId] = useState();

    const defaultZoom = window.innerWidth < 900 ? 7 : 9;
    const height = window.innerWidth < 900 ? "400px" : "750px";
    const center = [50.15, 4.8];
    const maxBounds = [
        [54, 10],
        [46, 0],
    ];
    const defaultPathOption = { weight: 1.5, color: "#DE007B", fillOpacity: 0.1 };
    const selectedPathOption = { weight: 1.5, color: "#DE007B", fillOpacity: 0.8 };

    useEffect(() => {
        axios
            .get(get_bundle_url() + "/assets/wallonia-boundaries.json")
            .then((response) => setRegionBoundaries(response.data));
        axios
            .get(get_portal_url() + "/@@institution_locations")
            .then((response) => setInstitutionLocations(response.data));
    }, []);

    const resetSelectedInstitutionId = useCallback(() => {
        setSelectedInstitutionId(null);
    }, []);

    return (
        <ReactLeaflet>
            {({ MapContainer, TileLayer, ZoomControl, GeoJSON, Popup }) => {
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
                        <ZoomControl position={"bottomright"} />
                        <TileLayer
                            attribution='Carte &copy; <a href="http://osm.org/copyright">OpenStreetMap</a> | Données &copy; <a href="https://www.ngi.be/website/fr/">NGI-IGN</a> '
                            url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
                        />
                        {regionBoundaries && <Mask data={regionBoundaries} />}
                        {institutionLocations &&
                            Object.keys(institutionLocations).map((institutionId) => {
                                const institution = institutionLocations[institutionId];
                                return (
                                    <GeoJSON
                                        key={institutionId}
                                        pathOptions={
                                            institutionId === selectedInstitutionId
                                                ? selectedPathOption
                                                : defaultPathOption
                                        }
                                        data={institution["data"]["fields"]["geo_shape"]}
                                        eventHandlers={{
                                            click: () => {
                                                setSelectedInstitutionId(institutionId);
                                            },
                                        }}
                                    >
                                        <Popup
                                            closeButton={false}
                                            onClose={resetSelectedInstitutionId}
                                        >
                                            <a
                                                className={"text-primary"}
                                                style={{
                                                    display: "flex",
                                                    justifyContent: "center",
                                                }}
                                                href={institution["URL"]}
                                            >
                                                {institution["data"]["fields"]["mun_name_fr"]}
                                                <CircleChevronRight
                                                    style={{ fill: "#DE007B" }}
                                                    height={15}
                                                    viewBox="0 0 24 24"
                                                />
                                            </a>
                                        </Popup>
                                    </GeoJSON>
                                );
                            })}
                    </MapContainer>
                );
            }}
        </ReactLeaflet>
    );
};

export default InstitutionsMap;
