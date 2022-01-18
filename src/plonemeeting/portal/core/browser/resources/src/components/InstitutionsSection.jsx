import { createContext, h } from "preact";
import { useMemo, useState } from "preact/hooks";
import InstitutionSelect from "./InstitutionSelect";
import InstitutionsMap from "./InstitutionsMap";

export const InstitutionsContext = createContext({});

const InstitutionsContextProvider = ({ children }) => {
    const [selectedInstitution, setSelectedInstitution] = useState();
    const value = {
        selectedInstitution,
        setSelectedInstitution,
    };
    return <InstitutionsContext.Provider value={value}>{children}</InstitutionsContext.Provider>;
};

const InstitutionSection = (props) => {
    const institutions = useMemo(() => JSON.parse(props["data-institutions"]), props);

    return (
        <InstitutionsContextProvider>
            <section className="hero-primary full-width">
                <div className="row">
                    <div className="col-lg-3">
                        <img
                            className="hero-img"
                            src="++plone++plonemeeting.portal.core/assets/delibe.svg"
                            alt="illustration"
                        />
                    </div>
                    <div className="col-lg-6">
                        <div className="hero-content">
                            <h1>Je cherche les décisions prises à...</h1>
                        </div>
                        <InstitutionSelect institutions={institutions} />
                    </div>
                    <div className="col-xl-3"></div>
                </div>
            </section>

            <section className="institutions-map-section full-width">
                <h2 className="text-primary">
                    Couverture géographique
                    <img
                        src="++plone++plonemeeting.portal.core/assets/marker-zone.svg"
                        alt="Map icon"
                    />
                </h2>
                <InstitutionsMap />
            </section>
        </InstitutionsContextProvider>
    );
};

export default InstitutionSection;
