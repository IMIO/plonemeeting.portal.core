import { h } from "preact";

/**
 * A map legend for institutions map
 */
const Legend = () => (
    <div className="leaflet-bottom leaflet-left leaflet-legend leaflet-box-control">
        <ul className="leaflet-legend-items">
            <li className="leaflet-legend-item">
                <div className="square square-inprogress" /> En cours
            </li>
            <li className="leaflet-legend-item">
                <div className="square square-published" /> Publié
            </li>
        </ul>
    </div>
);

export default Legend;
