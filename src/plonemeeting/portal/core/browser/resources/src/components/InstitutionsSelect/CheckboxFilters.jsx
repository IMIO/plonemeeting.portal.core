import { Fragment, h, render } from "preact";
import { useState, useEffect } from "preact/hooks";

const CheckboxFilters = ({ options, onChange }) => {
    return (
        <div className="checkbox-filter-select">
            {opt.map((o) => (
                <div className="option">
                    <input name={o} onChange={handleChange} type="checkbox" />
                    <span>{o}</span>
                </div>
            ))}
        </div>
    );
};

export default CheckboxFilters;
