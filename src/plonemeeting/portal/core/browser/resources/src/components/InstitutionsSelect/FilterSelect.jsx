import { createContext } from "preact";
import { useState, useContext, useMemo } from "preact/hooks";
import loadable from "@loadable/component";
import { components, createFilter } from "react-select";
const Select = loadable(() => import("react-select"));
import pickBy from "lodash/pickBy";
import isEmpty from "lodash/isEmpty";

/**
 * A filter context (shared state between a parent component and his children).
 * This is used to keep track of the filters checked by the user
 * to apply the filtering logic (see the `FilterSelect` component).
 * @type {PreactContext}
 */
const FilterContext = createContext({});

/**
 * Custom Menu for react-select that shows a list of checkboxes at the top.
 * @param props {object} React-select `components.Menu` props that will be used.
 * @component
 */
const FilterMenu = (props) => {
    const { filters, toggleFilter } = useContext(FilterContext);
    const handleClick = (event) => {
        event.preventDefault();
        event.stopPropagation();
        toggleFilter(event.target.name);
    };
    const handleLabelClick = (event) => {
        // This will prevent the loss of focus when clicking on a label,
        // which has the unfortunate effect of closing the select.
        event.preventDefault();
        event.stopPropagation();
        toggleFilter(event.target.attributes["name"].value);
    };
    return (
        <components.Menu {...props}>
            <fieldset className="checkbox-filter-select">
                {Object.entries(filters).map(([key, filter]) => (
                    <div className="option" key={key}>
                        <input
                            id={key}
                            name={key}
                            onChange={handleClick}
                            onTouchEnd={handleClick}
                            type="checkbox"
                            checked={filter.checked}
                        />
                        <label
                            name={key}
                            onClick={handleLabelClick}
                            onTouchEnd={handleLabelClick}
                            htmlFor={key}
                        >
                            {filter.label}
                        </label>
                    </div>
                ))}
            </fieldset>
            {props.children}
        </components.Menu>
    );
};

const defaultFilter = createFilter(); // default filter from react-select

/**
 * Represent a single filter. It has a label and a check value.
 * @typedef {object} Filter
 * @property {string} label
 * @property {boolean} checked
 */

/**
 * Represent a collection of filters in the form of a simple js object.
 * @typedef {object} FilterSelectProps
 * @property {Filter} *
 */
/**
 * React-select wrapper that contains the filtering logic.
 * @param {FilterSelectProps} filters
 * @param {object} props React-select `Select` props that will be used.
 * @component
 */
const FilterSelect = ({ filters: filtersProp, ...props }) => {
    const [filters, setFilters] = useState(filtersProp);

    const isAllDeselected = useMemo(
        () => isEmpty(pickBy(filters, (filter) => filter.checked)),
        [filters]
    );

    /**
     * First, we apply our filtering logic (no filter => display everything, else filter accordingly)
     * Then, we use the default filter (because it does some interesting things,
     * like normalizing the input from the search field).
     * @param label {string} Option label.
     * @param value {string} Option id. Not used for our filtering logic.
     * @param data {object} extra info set on a select option.
     * @param input {string} What the user has typed in the search field.
     * @returns {boolean}
     */
    const filterOptions = ({ label, value, data }, input) => {
        if (!isAllDeselected && filters[data.type] && !filters[data.type].checked) {
            return false;
        }
        return defaultFilter({ label, value, data }, input);
    };

    /**
     * Toggle given filter `key`.
     * @param key
     */
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
            <Select {...props} components={{ Menu: FilterMenu }} filterOption={filterOptions} />
        </FilterContext.Provider>
    );
};

export default FilterSelect;
