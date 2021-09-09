import { Fragment, h, render } from "preact";
import { useState } from "preact/hooks";
import Select from "react-select";
import RightArrowSVG from "../../assets/arrow-right.svg";

const InstitutionSelect = (props) => {
    const [selected, setSelected] = useState({});

    const institutions = JSON.parse(props["data-institutions"]);

    const handleChange = (option) => {
        setSelected(institutions[option.value]);
    };
    const options = Object.keys(institutions).map((key) => {
        return { value: key, label: institutions[key].title };
    });
    return (
        <Fragment>
            <div style={{ width: "375px" }}>
                <Select
                    isSearchable
                    options={options}
                    theme={(theme) => ({
                        ...theme,
                        colors: {
                            ...theme.colors,
                            primary75: "#f1f1f1",
                            primary50: "#DE007B21",
                            primary25: "#f1f1f1",
                            primary: "#DE007B",
                        },
                    })}
                    onChange={handleChange}
                    placeholder={"Sélectionner une ville/commune"}
                    noOptionsMessage={() => <span>Aucun résulat</span>}
                    autoBlur
                />
            </div>
            <a
                className={`btn btn-white ${_.isEmpty(selected) && "v-hidden"}`}
                href={selected.URL}
                role="button"
                aria-disabled={!_.isEmpty(selected)}
                aria-hidden={_.isEmpty(selected)}
            >
                <RightArrowSVG />
            </a>
        </Fragment>
    );
};

export default InstitutionSelect;
