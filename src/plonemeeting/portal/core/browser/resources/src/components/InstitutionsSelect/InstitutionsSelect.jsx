import { Fragment, h, render } from "preact";
import { useState, useEffect } from "preact/hooks";
import loadable from "@loadable/component";
import RightArrowSVG from "../../../assets/arrow-right.svg";
import { theme as imioTheme, style as imioStyle } from "./theme";
import _ from "lodash";
import FilterSelect from "./FilterSelect.jsx";

const InstitutionsSelect = (props) => {
    const institutions = JSON.parse(props["data-institutions"]);
    const institution_type = JSON.parse(props["data-institution-type-vocabulary"]);
    const [selected, setSelected] = useState({});
    const [groupedOptions, setGroupedOptions] = useState([]);
    const [filters, setFilters] = useState({});

    useEffect(() => {
        const filters = {};
        const groupedOptions = [];

        Object.entries(institutions).forEach(([key, institution]) => {
            const type = institution.institution_type;
            if (!filters.hasOwnProperty(type.token)) {
                filters[type.token] = {
                    label: type.title,
                    checked: true,
                };
                groupedOptions.push({
                    label: type.title,
                    options: [],
                });
            }
            groupedOptions[_.findIndex(groupedOptions, { label: type.title })].options.push({
                value: key,
                label: institution.title,
                type: type.token,
            });
        });
        setFilters(filters);
        setGroupedOptions(groupedOptions);
    }, []);

    const handleChange = (option) => {
        setSelected(institutions[option.value]);
    };

    return (
        <Fragment>
            <div style={{ width: "500px" }}>
                {!_.isEmpty(filters) && !_.isEmpty(groupedOptions) && (
                    <FilterSelect
                        isSearchable
                        options={groupedOptions}
                        filters={filters}
                        theme={imioTheme}
                        styles={imioStyle}
                        onChange={handleChange}
                        placeholder={"Sélectionner"}
                        noOptionsMessage={() => <span>Aucun résulat</span>}
                        autoBlur
                    />
                )}
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
