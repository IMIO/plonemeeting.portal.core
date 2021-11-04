import { h } from "preact";
import { GeoJSON, Popup } from "react-leaflet";
import { useCallback, useEffect, useState } from "preact/hooks";
import { memo, useRef } from "preact/compat";
import CircleChevronRight from "../../../assets/circle-chevron-right.svg";

const pathOptionsColor = {
    private: "#808080",
    published: "#DE007B",
};

/**
 * A map legend for institutions map
 */
const Institution = memo(({ geoShape, institution, selected, onClick }) => {
    const defaultPathOption = { weight: 1.5, fillOpacity: 0.1 };
    const [isHighlighted, setIsHighlighted] = useState();
    const geoJSONRef = useRef();
    const getPathOptionForInstitution = () => {
        return {
            ...defaultPathOption,
            fillOpacity: isHighlighted ? 0.8 : 0.1,
            color: pathOptionsColor[institution["state"]],
        };
    };

    const handleClick = useCallback(() => {
        setIsHighlighted(true);
        if (institution["state"] === "published") {
            onClick({ value: institution["id"], label: institution["title"] });
        }
    }, [institution, onClick]);

    const handleClose = useCallback(() => {
        setIsHighlighted(false);
    }, []);

    useEffect(() => {
        if (!isHighlighted && selected) {
            setIsHighlighted(true);
        } else if (isHighlighted && !selected) {
            setIsHighlighted(false);
            geoJSONRef.current.closePopup();
        }
    }, [selected]);

    return (
        <GeoJSON
            eventHandlers={{
                click: handleClick,
            }}
            pathOptions={getPathOptionForInstitution()}
            data={geoShape}
            ref={geoJSONRef}
        >
            <Popup onClose={handleClose} closeButton={false}>
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
});

export default Institution;
