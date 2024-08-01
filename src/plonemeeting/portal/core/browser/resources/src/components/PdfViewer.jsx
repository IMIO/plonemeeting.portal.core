import { useState, useRef } from "react";
import { usePdf } from "@mikecousins/react-pdf";
import { useEffect } from "preact/hooks";
import { get_bundle_url } from "../utils";

const PdfViewer = ({ file }) => {
    const [page, setPage] = useState(1);
    const [rotate, setRotate] = useState(0);
    const [scale, setScale] = useState(1);
    const [fullWidth, setFullWidth] = useState(false);
    const [fullScreen, setfullScreen] = useState(false);
    const canvasRef = useRef(null);
    const iframeRef = useRef(null);

    const { pdfDocument, pdfPage } = usePdf({
        file,
        page,
        rotate,
        scale: scale * 2,
        canvasRef,
    });

    const handlePrint = () => {
        iframeRef.current.src = file;
        iframeRef.current.addEventListener(
            "load",
            function () {
                iframeRef.current.contentWindow.print();
            },
            { once: true }
        );
    };

    const handleFullWidth = (event) => {
        if (fullWidth) {
            setScale(1);
            setTimeout(() => setFullWidth(false), 100); // Avoid flickering effect
        } else {
            setFullWidth(true);
            setScale(3);
        }
    };

    const handleFullScreen = () => {
        setfullScreen(!fullScreen);
    };

    const handleScaleIncrease = (event) => {
        if (fullWidth) {
            setScale(2);
            setTimeout(() => setFullWidth(false), 100); // Avoid flickering effect
        } else if (!isMaxScale(scale)) {
            setScale(scale + 0.25);
        }
    };

    const handleScaleDecrease = (event) => {
        if (fullWidth) {
            setScale(0.75);
            setTimeout(() => setFullWidth(false), 100); // Avoid flickering effect
        } else if (!isMinScale(scale)) {
            setScale(scale - 0.25);
        }
    };

    const isMaxScale = (scale) => scale >= 3;

    const isMinScale = (scale) => scale <= 0.25;

    return (
        <>
            <div className={`pdf-viewer ${fullScreen ? "pdf-viewer-full-screen" : ""}`}>
                {Boolean(pdfDocument && pdfDocument.numPages) && (
                    <nav className="pdf-viewer-toolbar">
                        <div className="pdf-viewer-toolbar-left">
                            <a
                                className="btn"
                                href="http://localhost:8080/conseil/liege/24-juin-2024-17-00/chr-de-la-citadelle-ago-du-28-juin-2024-approbation-des-points-portes-a-lordre-du-jour/document-soumis-au-conseil-1"
                            >
                                <i class="bi bi-file-earmark-arrow-down"></i>
                            </a>
                            <button className="btn" onClick={handlePrint}>
                                <i class="bi bi-printer"></i>
                            </button>
                        </div>

                        <div className="pdf-viewer-toolbar-center">
                            <button
                                className="btn"
                                disabled={page === 1}
                                onClick={() => setPage(page - 1)}
                            >
                                <i class="bi bi-chevron-left"></i>
                            </button>

                            <div class="">
                                {page} / {pdfDocument.numPages}
                            </div>

                            <button
                                className="btn"
                                disabled={page === pdfDocument.numPages}
                                onClick={() => setPage(page + 1)}
                            >
                                <i class="bi bi-chevron-right"></i>
                            </button>
                        </div>
                        <div className="pdf-viewer-toolbar-right">
                            <div
                                class="btn-group border-end"
                                role="group"
                                aria-label="Basic example"
                            >
                                <button className="btn" onClick={() => setRotate(rotate + 90)}>
                                    <i class="bi bi-arrow-clockwise"></i>
                                </button>
                            </div>

                            <button className="btn border-end" onClick={handleFullWidth}>
                                {!fullWidth && <i class="bi bi-arrows-expand-vertical"></i>}
                                {fullWidth && <i class="bi bi-arrows-collapse-vertical"></i>}
                            </button>

                            <div
                                class="btn-group border-end"
                                role="group"
                                aria-label="Basic example"
                            >
                                <button className="btn" onClick={handleScaleIncrease}>
                                    <i class="bi bi-plus-lg"></i>
                                </button>
                                <button className="btn" onClick={handleScaleDecrease}>
                                    <i class="bi bi-dash-lg"></i>
                                </button>
                            </div>

                            <button className="btn" onClick={handleFullScreen}>
                                {!fullScreen && <i class="bi bi-arrows-fullscreen"></i>}
                                {fullScreen && <i class="bi bi-x-lg"></i>}
                            </button>
                        </div>
                    </nav>
                )}
                <iframe
                    ref={iframeRef}
                    name="document-frame"
                    id="document-frame"
                    style={{ display: "none" }}
                ></iframe>

                <div class="pdf-viewer-page-viewport">
                    <div className="pdf-viewer-page-container">
                        {!pdfDocument && (
                            <img
                                src={get_bundle_url() + "/assets/ajax-spinner.svg"}
                                alt="loading..."
                            />
                        )}
                        {pdfDocument && (
                            <canvas className={fullWidth ? "pdf-full-width" : ""} ref={canvasRef} />
                        )}
                    </div>
                </div>
            </div>
            {fullScreen && (
                <button
                    className="pdf-viewer-full-screen-overlay"
                    onClick={handleFullScreen}
                ></button>
            )}
        </>
    );
};

export default PdfViewer;
