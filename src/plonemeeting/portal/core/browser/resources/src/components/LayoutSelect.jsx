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
    };

    const handleClick = (type) => {
        applyLayout(type);
        setActive(type);
        document.dispatchEvent(new Event("ItemsLayoutChanged"));
    };

    const cssClass = (type) => {
        return type === active ? "btn-delib active" : "btn-delib";
    };

    return (
        <div class="btn-group-delib" role="group" aria-label="Layout selection">
            <button type="button" className={cssClass("list")} onClick={() => handleClick("list")}>
                <i className="bi bi-list"></i>
            </button>
            <button type="button" className={cssClass("grid")} onClick={() => handleClick("grid")}>
                <i className="bi bi-grid"></i>
            </button>
        </div>
    );
};

export default LayoutSelect;
