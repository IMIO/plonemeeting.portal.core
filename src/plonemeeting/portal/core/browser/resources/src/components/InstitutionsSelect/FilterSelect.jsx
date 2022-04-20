import { createContext, Fragment, h, render } from "preact";
import { useState, useEffect, useContext } from "preact/hooks";
import loadable from "@loadable/component";
import { components, createFilter } from "react-select";
import CheckboxFilters from "./CheckboxFilters";
import makeAnimated from "react-select/animated";
const Select = loadable(() => import("react-select"));

const FilterMenu = (props) => {
    const { filters, toggleFilter } = useContext(FilterContext);
    const handleChange = (event) => {
        toggleFilter(event.target.name);
    };
    return (
        <components.Menu {...props}>
            <div className="checkbox-filter-select">
                {Object.entries(filters).map(([key, filter]) => (
                    <div className="option" key={key}>
                        <input
                            name={key}
                            onChange={handleChange}
                            type="checkbox"
                            checked={filter.checked}
                        />
                        <span>{filter.label}</span>
                    </div>
                ))}
            </div>
            {props.children}
        </components.Menu>
    );
};

const defaultFilter = createFilter();
const FilterOptions = (props) => {
    const { filters } = useContext(FilterContext);

    const filterOptions = ({ label, value, data }, input) => {
        if (filters[data.type] && !filters[data.type].checked) {
            return false;
        }
        return defaultFilter({ label, value, data }, input);
    };
    return <Select {...props} components={{ Menu: FilterMenu }} filterOption={filterOptions} />;
};

const FilterContext = createContext(null);

const FilterSelect = (props) => {
    const [filters, setFilters] = useState(props.filters);
    const toggleFilter = (key) => {
        setFilters({
            ...filters,
            [key]: {
                ...filters[key],
                checked: !filters[key].checked,
            },
        });
    };

    return (
        <FilterContext.Provider value={{ filters, toggleFilter }}>
            <FilterOptions {...props}></FilterOptions>
        </FilterContext.Provider>
    );
};

export default FilterSelect;
