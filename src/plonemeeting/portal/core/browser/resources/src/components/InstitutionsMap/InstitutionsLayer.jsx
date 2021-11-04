import { Fragment, h } from "preact";
import { useContext } from "preact/hooks";
import { LayerGroup } from "react-leaflet";
import { InstitutionsContext } from "../InstitutionsSection";

import Institution from "./Institution";

/**
 * A map legend for institutions map
 */
const InstitutionsLayer = ({ institutions, state }) => {
    const { selectedInstitution, setSelectedInstitution } = useContext(InstitutionsContext);
    return (
        <LayerGroup>
            {Object.keys(institutions).map((key) => (
                <Institution
                    key={key}
                    state={institutions[key]["state"]}
                    geoShape={institutions[key]["data"]["fields"]["geo_shape"]}
                    institution={institutions[key]}
                    selected={selectedInstitution?.value === key}
                    onClick={setSelectedInstitution}
                />
            ))}
        </LayerGroup>
    );
};

export default InstitutionsLayer;
