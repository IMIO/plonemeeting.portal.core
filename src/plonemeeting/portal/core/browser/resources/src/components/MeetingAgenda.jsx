import {useEffect, useState} from "preact/hooks";
import axios from "axios";
import {randomInt} from "../utils";

const placeHolderVariations = [
    [2, 1, 4, 3],
    [4, 2, 2, 1, 2],
    [1, 3, 2, 1, 2],
    [4, 1, 2, 1, 2],
    [1, 2, 4, 5, 2],
    [1, 1, 4, 1, 2],
    [4, 1, 3, 1, 2],
    [1, 1, 2, 1, 2],
];
const MeetingAgendaPlaceHolder = ({count}) => {
    const rows = randomInt(1, 3);

    return (
        <li>
            <a className="item-line placeholder-glow" href="">
                <span className="item-number">{count}</span>
                <span className="item-title">
                    {[...Array(rows)].map((x, i) =>
                        placeHolderVariations[randomInt(0, placeHolderVariations.length)].map(
                            (col, j) => (
                                <span className={`placeholder col-${col} mx-1`} key={j}></span>
                            )
                        )
                    )}
                </span>
            </a>
        </li>
    );
};

const MeetingAgenda = ({count, meetingUrl}) => {
    const [items, setItems] = useState();
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState();
    const [offcanvas, setOffcanvas] = useState(false);

    useEffect(() => {
        setOffcanvas(new bootstrap.Offcanvas(document.getElementById("meeting-agenda")));
    }, []);

    const handleClick = () => {
        offcanvas.toggle();
        axios
            .get(meetingUrl + "/@@agenda")
            .then((response) => {
                setItems(response.data);
                setIsLoading(false);
            })
            .catch(handleError);
    };

    const handleError = (error) => {
        console.error(error);
        setIsLoading(false);
        setError(error);
    };

    return (
        <>
            <button
                className="btn btn-link"
                type="button"
                onClick={handleClick}
                aria-controls="meeting-agenda"
            >
                <i class="bi bi-list-ol" style={{
                    marginBottom: "-2px",
                    padding: "0 5px"
                }}></i><span className="d-none d-md-inline">Ordre du jour</span>
            </button>
            <div
                class="offcanvas offcanvas-end"
                tabIndex="-1"
                id="meeting-agenda"
                aria-labelledby="meeting-agenda"
            >
                <div class="offcanvas-header">
                    <h3 class="offcanvas-title" id="offcanvas-agenda">
                        Ordre du jour
                    </h3>
                    <button
                        type="button"
                        className="btn-close"
                        data-bs-dismiss="offcanvas"
                        aria-label="Close"
                    ></button>
                </div>
                <div class="offcanvas-body">
                    <ul className="items-list">
                        {isLoading &&
                            [...Array(parseInt(count))].map((x, i) => (
                                <MeetingAgendaPlaceHolder number={i + 1} key={i}/>
                            ))}
                        {!isLoading && (
                            <>
                                {items &&
                                    items.map((item, index) => (
                                        <li>
                                            <a className="item-line" href={item["@id"]}>
                                                <span className="item-number">{item.number}</span>
                                                <span className="item-title">
                                                    <div
                                                        dangerouslySetInnerHTML={{
                                                            __html: item.formatted_title.data,
                                                        }}
                                                    ></div>
                                                </span>
                                            </a>
                                        </li>
                                    ))}
                            </>
                        )}
                    </ul>
                </div>
            </div>
        </>
    );
};

export default MeetingAgenda;
