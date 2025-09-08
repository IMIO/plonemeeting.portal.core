import { useState, useRef } from "react";
import { usePdf } from "@mikecousins/react-pdf";
import { useEffect } from "preact/hooks";
import { get_bundle_url } from "../utils";
import printJS from "print-js-updated";

const PdfViewer = ({ file }) => {
    const [page, setPage] = useState(1);
    const [rotate, setRotate] = useState(0);
    const [scale, setScale] = useState(1);
    const [fullWidth, setFullWidth] = useState(true);
    const [fullScreen, setfullScreen] = useState(false);
    const [scrollingOver, setScrollingOver] = useState(false);
    const canvasRef = useRef(null);

    const { pdfDocument, pdfPage } = usePdf({
        file,
        page,
        rotate,
        scale: scale * 2,
        canvasRef,
    });

    useEffect(() => {
        window.addEventListener("scroll", () => {
            if (canvasRef.current) {
                const rect = canvasRef.current.getBoundingClientRect();
                setScrollingOver(rect.top < 150 && rect.bottom > 0);
            }
        });
    }, []);

    const handlePrint = () => {
        printJS({ printable: file, type: "pdf" });
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
        setScrollingOver(false);
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
            <div className={`pdf-viewer  ${fullScreen ? "pdf-viewer-full-screen" : ""}`}>
                {Boolean(pdfDocument && pdfDocument.numPages) && (
                    <nav
                        className={`pdf-viewer-toolbar ${
                            !fullScreen && scrollingOver ? "fixed-toolbar" : ""
                        }`}
                    >
                        <div className="pdf-viewer-toolbar-left">
                            <div className="btn-group">
                                <a
                                    className="btn"
                                    href={file}
                                    target="_blank"
                                    title="Télécharger le document"
                                >
                                    <i class="bi bi-file-earmark-arrow-down"></i>
                                </a>
                                <button
                                    className="btn"
                                    onClick={handlePrint}
                                    title="Imprimer le document"
                                >
                                    <i class="bi bi-printer"></i>
                                </button>
                            </div>
                        </div>

                        <div className="pdf-viewer-toolbar-center">
                            <button
                                className="btn"
                                disabled={page === 1}
                                onClick={() => setPage(page - 1)}
                                key={page - 1}
                                title="Page précédente"
                            >
                                <i class="bi bi-chevron-left"></i>
                            </button>

                            <div class="pdf-viewer-page-count">
                                {page} / {pdfDocument.numPages}
                            </div>

                            <button
                                className="btn"
                                disabled={page === pdfDocument.numPages}
                                onClick={() => setPage(page + 1)}
                                key={page + 1}
                                title="Page suivante"
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
                                <button
                                    className="btn"
                                    onClick={() => setRotate(rotate + 90)}
                                    title="Tourner la page"
                                >
                                    <i class="bi bi-arrow-clockwise"></i>
                                </button>
                            </div>

                            {!fullWidth && (
                                <div class="btn-group border-end">
                                    <button
                                        className="btn"
                                        onClick={handleFullWidth}
                                        title="Pleine largeur"
                                    >
                                        <i class="bi bi-arrows-expand-vertical"></i>
                                    </button>
                                </div>
                            )}

                            {fullWidth && (
                                <div class="btn-group border-end">
                                    <button
                                        className="btn"
                                        onClick={handleFullWidth}
                                        title="Réduire"
                                    >
                                        <i class="bi bi-arrows-collapse-vertical"></i>
                                    </button>
                                </div>
                            )}
                            <div class="btn-group border-end" role="group">
                                <button
                                    className="btn"
                                    onClick={handleScaleIncrease}
                                    title="Zoomer"
                                >
                                    <i class="bi bi-plus-lg"></i>
                                </button>
                                <button
                                    className="btn"
                                    onClick={handleScaleDecrease}
                                    title="Dézoomer"
                                >
                                    <i class="bi bi-dash-lg"></i>
                                </button>
                            </div>
                            <div class="btn-group" role="group">
                                {!fullScreen && (
                                    <button
                                        className="btn"
                                        onClick={handleFullScreen}
                                        title="Plein écran"
                                    >
                                        <i class="bi bi-arrows-fullscreen"></i>
                                    </button>
                                )}
                                {fullScreen && (
                                    <button
                                        className="btn"
                                        onClick={handleFullScreen}
                                        title="Fermer"
                                    >
                                        <i class="bi bi-x-lg"></i>
                                    </button>
                                )}
                            </div>
                        </div>
                    </nav>
                )}
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
