import { h } from "preact";
import CircleChevronRight from "../../../assets/circle-chevron-right.svg";
import { Popup } from "react-leaflet";
import { memo } from "preact/compat";

const InstitutionPopup = ({ institution, onClose }) => (
    <Popup closeButton={false} onClose={onClose}>
        <a
            className={"text-primary"}
            style={{
                display: "flex",
                justifyContent: "center",
            }}
            href={institution["URL"]}
        >
            {institution["data"]["fields"]["mun_name_fr"]}
            <CircleChevronRight style={{ fill: "#DE007B" }} height={15} viewBox="0 0 24 24" />
        </a>
    </Popup>
);
export default memo(InstitutionPopup, (prevProps, nextProps) => {
    return prevProps.institution["id"] === nextProps.institution["id"];
});
