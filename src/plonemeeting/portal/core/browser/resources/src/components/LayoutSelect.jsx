import {useEffect, useState} from "preact/hooks";

/**
 * Layout selector component
 * @param id The id of the layout to store in localStorage
 * @param targetSelector The selector of the element to apply the layout to
 * @param defaultOption The default layout to apply
 */
const LayoutSelect = ({id, targetSelector, defaultOption}) => {
    const [active, setActive] = useState(null);

    useEffect(() => {
        const layout = localStorage.getItem(id) ?? defaultOption;
        applyLayout(layout);
        setActive(layout);
    }, []);

    const applyLayout = (type) => {
        // Remove all classes and add the selected layout type.
        document.querySelector(targetSelector)?.classList.remove("list", "grid");
        document.querySelector(targetSelector)?.classList.add(type);
        localStorage.setItem(id, type);
    }

    const handleClick = (type) => {
        applyLayout(type);
        setActive(type);
        document.dispatchEvent(new Event('ItemsLayoutChanged'));

    }

    const cssClass = (type) => {
        return type === active ? "btn btn-light active" : "btn btn-light";
    }

    return (
        <div class="btn-group" role="group" aria-label="Layout selection">
            <button type="button" className={cssClass("list")} onClick={() => handleClick("list")}>
                <span className="icon-wrapper">
                    <i className="bi bi-list"></i>
                </span>
            </button>
            <button type="button" className={cssClass("grid")} onClick={() => handleClick("grid")}>
                <span className="icon-wrapper">
                    <i className="bi bi-grid"></i>
                </span>
            </button>
        </div>
    )
}

export default LayoutSelect;
