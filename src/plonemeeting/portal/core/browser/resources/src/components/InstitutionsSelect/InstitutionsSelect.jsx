import { Fragment, h, render } from "preact";
import { useState, useEffect } from "preact/hooks";
import loadable from "@loadable/component";
import RightArrowSVG from "../../../assets/arrow-right.svg";
import { theme as imioTheme, style as imioStyle } from "./theme";

import FilterSelect from "./FilterSelect.jsx";

const InstitutionsSelect = (props) => {
    const [selected, setSelected] = useState({});
    const [groupedOptions, setGroupedOptions] = useState([]);

    useEffect(() => {
        const options = Object.keys(institutions).map((key) => {
            return { value: key, label: institutions[key].title };
        });
        setGroupedOptions(options);
    }, []);

    const institutions = JSON.parse(props["data-institutions"]);

    const handleChange = (option) => {
        setSelected(institutions[option.value]);
    };

    return (
        <Fragment>
            <div style={{ width: "500px" }}>
                <FilterSelect
                    isSearchable
                    options={groupedOptions}
                    theme={imioTheme}
                    styles={imioStyle}
                    onChange={handleChange}
                    placeholder={"Sélectionner"}
                    noOptionsMessage={() => <span>Aucun résulat</span>}
                    autoBlur
                />
            </div>
            <a
                className="btn btn-white"
                href={selected["@id"]}
                role="button"
                aria-disabled={_.isEmpty(selected)}
            >
                <RightArrowSVG />
            </a>
        </Fragment>
    );
};

export default InstitutionsSelect;
