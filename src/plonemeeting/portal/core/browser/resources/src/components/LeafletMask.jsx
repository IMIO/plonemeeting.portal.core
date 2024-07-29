import { useLeafletContext } from "@react-leaflet/core";
import { useEffect } from "preact/hooks";
import L from "leaflet";

const defaultOptions = {
    stroke: false,
    color: "#000000",
    fillOpacity: 0.05,
    clickable: false,
    outerBounds: new L.LatLngBounds([-90, -360], [90, 360]),
};

/**
 * Leaflet component that will mask around the geoJSON passed in data props
 * You can pass L.Polygon props (see defaultOptions above) to tweak the mask rendering
 */
export function Mask(props) {
    const context = useLeafletContext();
    const { data, ...rest } = props;
    const options = {
        ...defaultOptions,
        ...rest,
    };

    useEffect(() => {
        const coordinates = data.geometry.coordinates;
        let latLngs = [];
        for (var i = 0; i < coordinates.length; i++) {
            latLngs.push(new L.LatLng(coordinates[i][1], coordinates[i][0]));
        }

        const outerBoundsLatLngs = [
            options.outerBounds.getSouthWest(),
            options.outerBounds.getNorthWest(),
            options.outerBounds.getNorthEast(),
            options.outerBounds.getSouthEast(),
        ];
        const poly = new L.Polygon([outerBoundsLatLngs, latLngs], options);
        const container = context.layerContainer || context.map;
        container.addLayer(poly);

        return () => {
            container.removeLayer(poly);
        };
    });
    return null;
}
