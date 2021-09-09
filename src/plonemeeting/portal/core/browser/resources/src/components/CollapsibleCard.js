import { Fragment, h, render } from "preact";
import { useState, useRef } from "preact/hooks";

const CollapsibleCard = (props) => {
    const [collapsed, setCollapsed] = useState(true);
    const collapsibleZone = useRef(null);

    const handleToggleClick = () => {
        jQuery(collapsibleZone.current).slideToggle("fast", function () {});
    };

    return (
        <article className="faq-item">
            <div className="faq-item-header">
                <button className="btn btn-primary" onClick={handleToggleClick}>
                    <h3 className="faq-item-title">Qu'est ce qu'un Conseil communal ?</h3>
                </button>
            </div>
            <div className={`faq-item-content`}>
                <div ref={collapsibleZone} style={{ padding: "2em" }}>
                    <p>
                        Le Conseil communal est l'<strong>organe législatif</strong> de la commune,
                        il constitue, comme le Collège communal et le bourgmestre, un organe
                        représentatif de toute la population de la commune.
                    </p>
                    <p>
                        Sauf exceptions, le Conseil communal se réunit, sur convocation du Collège
                        communal, chaque fois que les affaires comprises dans ses attributions le
                        nécessitent, et au moins dix fois par an.
                    </p>
                    <p>
                        Le conseil communal concentre les attributions les plus larges, il règle
                        tout ce qui n’est pas spécifiquement attribué à un autre organe de la
                        commune (par exemple : le vote du budget et du compte ; des taxes et
                        redevances, le vote des règlements ; la décision de participer à une
                        intercommunale ; les décisions patrimoniales, ...).
                    </p>
                    <p>
                        <strong>
                            Pour plus d'informations, nous vous proposons de consulter le site de
                            l’UVCW (Voir Focus sur la commune
                            <a href="https://www.uvcw.be/focus">https://www.uvcw.be/focus</a> et la
                            commune expliquée aux candidats et aux nouveaux élus{" "}
                            <a href="https://www.uvcw.be/publications/63">
                                https://www.uvcw.be/publications/63
                            </a>
                            ).
                        </strong>
                    </p>
                </div>
            </div>
        </article>
    );
};

export default CollapsibleCard;
