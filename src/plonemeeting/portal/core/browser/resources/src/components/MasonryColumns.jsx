import { useEffect } from "preact/hooks";
import Masonry from "masonry-layout";

/**
 * Simple wrapper around "masonry-layout" to create a vertical tiles layout
 */
const MasonryColumns = (props) => {
    useEffect(() => {
        const elem = document.querySelector(props["container-selector"]);
        const msnry = new Masonry(elem, {
            itemSelector: props["item-selector"],
            gutter: parseInt(props["gutter"]),
        });
        msnry.layout();
    }, []);
    return false;
};

export default MasonryColumns;
