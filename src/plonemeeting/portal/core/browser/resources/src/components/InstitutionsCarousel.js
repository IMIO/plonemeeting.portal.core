import { Fragment, h, render } from "preact";
import { useEffect, useState } from "preact/hooks";
// import Swiper JS
import { Swiper, SwiperSlide } from "swiper/react";
// import Swiper styles
import "swiper/css";

import "swiper/css/grid";

import SwiperCore, { Grid } from "swiper";
// install Swiper modules
SwiperCore.use([Grid]);

const InstitutionSelect = (props) => {
    const [institutions, setInstitutions] = useState();

    useEffect(() => {
        setInstitutions(JSON.parse(props["data-institutions"]));
    }, []);

    return (
        <div className="institution-carousel">
            {institutions && (
                <Swiper
                    grid={{
                        rows: 2,
                        fill: "row",
                    }}
                    pagination={{
                        clickable: true,
                    }}
                    breakpoints={{
                        // when window width is >= 320px
                        0: {
                            slidesPerView: 4,
                            spaceBetween: 5,
                        },
                        // when window width is >= 480px
                        480: {
                            slidesPerView: 5,
                            spaceBetween: 5,
                        },
                        // when window width is >= 640px
                        640: {
                            slidesPerView: 6,
                            spaceBetween: 5,
                        },
                        764: {
                            slidesPerView: 7,
                            spaceBetween: 10,
                        },
                        900: {
                            slidesPerView: 9,
                            spaceBetween: 20,
                        },
                        1200: {
                            slidesPerView: 12,
                            spaceBetween: 20,
                        },
                    }}
                >
                    {Object.keys(institutions).map((key) => (
                        <SwiperSlide>
                            <div className="institution-card">
                                <div className="institution-card-img">
                                    <img
                                        src={`http://localhost:8080/conseil/${key}/@@images/logo/thumb`}
                                    />
                                </div>
                                <div className="institution-card-label">
                                    {institutions[key].title}
                                </div>
                            </div>{" "}
                        </SwiperSlide>
                    ))}
                </Swiper>
            )}
        </div>
    );
};

export default InstitutionSelect;
