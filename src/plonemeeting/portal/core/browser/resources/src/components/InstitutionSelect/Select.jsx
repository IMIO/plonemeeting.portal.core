import { h } from "preact";
import { useContext, useMemo } from "preact/hooks";
import RightArrowSVG from "../../../assets/arrow-right.svg";
import { InstitutionsContext } from "../InstitutionsSection";
import Select from "react-select";

const InstitutionsSelect = ({ institutions }) => {
    const { selectedInstitution, setSelectedInstitution } = useContext(InstitutionsContext);

    const handleChange = (option) => {
        setSelectedInstitution(option);
    };
    const options = useMemo(
        () =>
            Object.keys(institutions).map((key) => {
                return { value: key, label: institutions[key].title };
            }),
        [institutions]
    );

    const applyCustomTheme = (base) => ({
        ...base,
        colors: {
            ...base.colors,
            primary75: "#f1f1f1",
            primary50: "#DE007B21",
            primary25: "#f1f1f1",
            primary: "#DE007B",
        },
    });

    return (
        <div className="institution-select">
            <div className="institution-select-input">
                <Select
                    value={selectedInstitution}
                    isSearchable
                    options={options}
                    theme={applyCustomTheme}
                    onChange={handleChange}
                    placeholder={"Sélectionner une administration"}
                    noOptionsMessage={() => <span>Aucun résulat</span>}
                    autoBlur
                />
            </div>
            <a
                className="btn btn-white"
                href={selectedInstitution?.URL}
                role="button"
                aria-disabled={_.isEmpty(selectedInstitution)}
            >
                <RightArrowSVG />
            </a>
        </div>
    );
};

export default InstitutionsSelect;
