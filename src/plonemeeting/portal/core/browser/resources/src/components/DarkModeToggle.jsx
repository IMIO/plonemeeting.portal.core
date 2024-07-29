import {useEffect, useState} from "preact/hooks";

/**
 * Layout selector component
 */
const DarkModeToggle = () => {
    const [active, setActive] = useState(null);

    useEffect(() => {
        const layout = localStorage.getItem("dark-mode");
        if (layout) {
            setActive(layout);
        } else {
            setActive("light");
        }
    }, []);

    useEffect(() => {
        // Apply layout each time active changes
        applyLayout(active);
    }, [active]);

    const applyLayout = (type) => {
        // Remove all classes and add the selected layout type.
        document.querySelector("body").classList.remove("light", "dark");
        document.querySelector("body").classList.add(type);
        document.querySelector("html").setAttribute('data-bs-theme', type);
        localStorage.setItem("dark-mode", type);
    }

    const handleToggle = () => {
            active === "dark" ? setActive("light") : setActive("dark");
    }

    const cssClass = (type) => {
        return type === active ? "btn btn-light" : "btn btn-dark";
    }

    return (
        <div className="form-check form-switch">
            <input className="form-check-input" type="checkbox" role="switch" id="flexSwitchCheckDefault"
                   onClick={handleToggle}/>
        </div>
    )
}

export default DarkModeToggle;
