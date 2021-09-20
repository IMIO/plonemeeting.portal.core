import { Fragment, h, render } from "preact";
import { useState } from "preact/hooks";
import loadable from '@loadable/component'
import RightArrowSVG from "../../assets/arrow-right.svg";

const Select = loadable(() => import('react-select'))

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
            <div className="institution-select-input">
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
                className="btn btn-white"
                href={selected.URL}
                role="button"
                aria-disabled={_.isEmpty(selected)}
            >
                <RightArrowSVG />
            </a>
        </Fragment>
    );
};

export default InstitutionSelect;
