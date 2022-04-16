import { Fragment, h, render } from "preact";
import { useState, useEffect } from "preact/hooks";
import loadable from "@loadable/component";
import { components } from "react-select";
import CheckboxFilters from "./CheckboxFilters";

const Select = loadable(() => import("react-select"));

const FilterMenu = (props) => {
    return (
        <Fragment>
            <components.Menu {...props}>
                <CheckboxFilters />
                {props.children}
            </components.Menu>
        </Fragment>
    );
};

const FilterSelect = (props) => {
    return <Select {...props} components={{ Menu: FilterMenu }} />;
};

export default FilterSelect;
