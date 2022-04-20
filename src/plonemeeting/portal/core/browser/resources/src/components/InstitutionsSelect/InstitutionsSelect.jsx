import { Fragment, h, render } from "preact";
import { useState, useEffect } from "preact/hooks";
import loadable from "@loadable/component";
import RightArrowSVG from "../../../assets/arrow-right.svg";
import { theme as imioTheme, style as imioStyle } from "./theme";
import _ from "lodash";
import FilterSelect from "./FilterSelect.jsx";

const InstitutionsSelect = (props) => {
    const [selected, setSelected] = useState({});
    const [institutions, setInstitutions] = useState();
    const [groupedOptions, setGroupedOptions] = useState([]);
    const [filters, setFilters] = useState({});

    useEffect(() => {
        let filters = {};
        let groupedOptions = [];
        const institutions = JSON.parse(props["data-institutions"]);
        const institution_type_vocabulary = JSON.parse(props["data-institution-type-vocabulary"]);
        institution_type_vocabulary.items.forEach((type) => {
            groupedOptions.push({
                label: type.title,
                id: type.token,
                options: [],
            });
            if (!filters.hasOwnProperty(type.token)) {
                filters[type.token] = {
                    label: type.title,
                    checked: true,
                };
            }
        });

        Object.entries(institutions).forEach(([key, institution]) => {
            const type = institution.institution_type;
            groupedOptions[_.findIndex(groupedOptions, { label: type.title })].options.push({
                value: key,
                label: institution.title,
                type: type.token,
            });
        });

        filters = _.omitBy(filters, (filter) => {
            return (
                groupedOptions[_.findIndex(groupedOptions, { label: filter.label })].options
                    .length === 0
            );
        });
        setInstitutions(institutions);
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
