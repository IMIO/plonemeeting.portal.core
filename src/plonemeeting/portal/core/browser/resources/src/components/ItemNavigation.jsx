import {useEffect, useState} from "preact/hooks";
import axios from "axios";


const ItemNavigation = () => {

    const [navigationInfos, setNavigationInfos] = useState({
        count: 0, current: 0, previous: null, next: null
    });


    useEffect(() => {
        // Fetch navigation infos
        // This is just a placeholder, you should replace this with your own implementation
        axios.get(document.URL + "/@@navigation-infos")
            .then((response) => setNavigationInfos(response.data));
    }, []);


    return (
            <span class="dropdown navigation-dropdown">
                <button className="btn btn-light delib-btn dropdown-toggle" type="button" data-bs-toggle="dropdown"
                        aria-expanded="false">
                    <i className="bi bi-list-ol"></i>
                </button>
                <ul class="dropdown-menu items-list">
                    <li><a className="item-line" href="#">
                        <span class="item-number">1</span>
                        <span class="item-title">Lorem ipsum amet, consectetur adipisicing elit.</span>
                    </a>
                    </li>
                                        <li><a className="item-line" href="#">
                        <span class="item-number">2</span>
                        <span class="item-title">Lorem ipsum dolor amet,  consectetur adipisicing elit. Lorem ipsum dolor amet,  consectetur adipisicing elit.</span>
                    </a>
                    </li>
                                        <li><a className="item-line" href="#">
                        <span class="item-number">3</span>
                        <span class="item-title">Lorem ipsum dolor Lorem ipsum dolor amet, consectetur adipisicing elit. sit amet, consectetur adipisicing elit. Lorem ipsum dolor amet,  consectetur adipisicing elit. Lorem ipsum dolor amet,  consectetur adipisicing elit.</span>
                    </a>
                    </li>
                                        <li><a className="item-line" href="#">
                        <span class="item-number">4</span>
                        <span class="item-title">Lorem ipsum dolor sit amet, consectetur adipisicing elit.</span>
                    </a>
                    </li>
                                        <li><a className="item-line" href="#">
                        <span class="item-number">56</span>
                        <span class="item-title">Lorem ipsum dolor sit amet, consectetur adipisicing elit.</span>
                    </a>
                    </li>
                                        <li><a className="item-line" href="#">
                        <span class="item-number">156.2</span>
                        <span class="item-title">Lorem ipsum dolor sit amet, consectetur adipisicing elit.</span>
                    </a>
                    </li>

                </ul>
            </span>
       )
}

export default ItemNavigation;
