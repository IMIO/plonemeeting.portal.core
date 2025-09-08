import React, {useState} from "react";
import JSZip from "jszip";
import {useDropzone} from "react-dropzone";
import classNames from "classnames";
import * as asn1js from "asn1js";
import {ContentInfo, SignedData, TSTInfo} from "pkijs";
import {useCallback} from "preact/hooks";

const HASH_OID_TO_NAME = {
    "1.3.14.3.2.26": "SHA‑1",
    "2.16.840.1.101.3.4.2.1": "SHA‑256",
    "2.16.840.1.101.3.4.2.2": "SHA‑384",
    "2.16.840.1.101.3.4.2.3": "SHA‑512",
};

// Extract a simple object (cn, country, locality, state …) from GeneralName
const parseGeneralNameDirectory = (gn) => {
    if (!gn || gn.type !== 4) return {};
    const dir = gn.value; // RelativeDistinguishedNames
    return {
        cn: getAttr(dir, "2.5.4.3"),
        o: getAttr(dir, "2.5.4.10"),
        ou: getAttr(dir, "2.5.4.11"),
        country: getAttr(dir, "2.5.4.6"),
        state: getAttr(dir, "2.5.4.8"),
        locality: getAttr(dir, "2.5.4.7"),
    };
};

const toHex = (buffer) =>
    Array.prototype.map
        .call(new Uint8Array(buffer), (x) => x.toString(16).padStart(2, "0"))
        .join("");

// Extract attribute by OID from a pkijs RelativeDistinguishedNames
const getAttr = (rdn, oid) => {
    const tv = rdn.typesAndValues.find((t) => t.type === oid);
    return tv ? tv.value.valueBlock.value : "";
};

const getCN = (rdn) => {
    return getAttr(rdn, "2.5.4.3");
};

const fmtBytes = (bytes) => {
    if (bytes === 0) return '0 o';
    const k = 1024;
    const sizes = ['o', 'Ko', 'Mo', 'Go'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// Sub-component to display the certificate table
const CertTable = ({certs}) => (
    <div className="table-responsive">
        <table className="table table-sm mb-0">
            <thead className="table-light">
            <tr>
                <th className="fw-semibold text-dark">#</th>
                <th className="fw-semibold text-dark">Sujet</th>
                <th className="fw-semibold text-dark">Émetteur</th>
                <th className="fw-semibold text-dark">Numéro de série</th>
                <th className="fw-semibold text-dark">Valide depuis</th>
                <th className="fw-semibold text-dark">Valide jusqu'au</th>
            </tr>
            </thead>
            <tbody>
            {certs.map((c) => (
                <tr key={c.idx}>
                    <td className="font-monospace small">{c.idx}</td>
                    <td className="font-monospace small">{c.subjectCN}</td>
                    <td className="font-monospace small">{c.issuerCN}</td>
                    <td className="text-monospace small">{c.serial}</td>
                    <td className="font-monospace small">{c.notBefore}</td>
                    <td className="font-monospace small">{c.notAfter}</td>
                </tr>
            ))}
            </tbody>
        </table>
    </div>
);

// Sub-component to display the embedded files in a scrollable table
const EmbeddedTable = ({files}) => (
    <div className="table-responsive" style={{fontSize: "0.9rem", maxHeight: "250px", overflowY: "auto"}}>
        <table className="table table-sm mb-0">
            <thead className="table-light sticky-top shadow-inner">
            <tr>
                <th className="fw-semibold text-dark">Nom de fichier</th>
                <th className="fw-semibold text-dark">Taille</th>
            </tr>
            </thead>
            <tbody>
            {files?.map((file, index) => (
                <tr key={index}>
                    <td className="font-monospace small">{file.name}</td>
                    <td className="font-monospace small">{fmtBytes(file.size)}</td>
                </tr>
            ))}
            </tbody>
        </table>
    </div>
);

// Sub-component to display the status of the verification
const CheckStatus = ({status, children}) => {
    const statusClass = classNames(status === "valid" ? "status-valid" : "status-invalid");
    const iconClass = classNames(status === "valid" ? "bi-check-circle" : "bi-x-circle");
    return (
        <div id="timestamp-status" className={`alert card text-white border-0 mb-0 ${statusClass}`} role="alert">
            <div className="d-flex align-items-center">
                <i className={`bi bi-patch-check-fill me-3 fs-2 ${iconClass}`}></i>
                {children}
            </div>
            <i className="icon-bg bi bi-watch fs-1"></i>
        </div>
    )
}

// Main component for timestamp verification
const TimestampCheck = () => {
    const [status, setStatus] = useState(null); // "valid" | "invalid" | null
    const [details, setDetails] = useState(null); // full report
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);

    const reset = () => {
        setStatus(null);
        setDetails(null);
        setError(null);
    };

    const verifyFile = async (file) => {
        try {
            setLoading(true);

            const outerZip = await JSZip.loadAsync(file);

            const tstEntry = outerZip.file("META-INF/timestamp.tst");
            if (!tstEntry) throw new Error("Le fichier META-INF/timestamp.tst n'est pas présent.");

            const manifestEntry = outerZip.file(/META-INF\/ASiCManifest.*\.xml/)[0];
            if (!manifestEntry) throw new Error("Le fichier ASiCManifest n'est pas présent.");
            const manifestText = await manifestEntry.async("text");
            const payloadName = /DataObjectReference\s+URI="([^"]+)"/.exec(
                manifestText
            )[1];

            const payloadEntry = outerZip.file(payloadName);
            if (!payloadEntry) throw new Error(`Le fichier ${payloadName} est manquant alors qu'il est référencé dans le manifeste.`);

            const [payloadBuffer, tstBuffer] = await Promise.all([
                payloadEntry.async("arraybuffer"),
                tstEntry.async("arraybuffer"),
            ]);

            // Let's try to load the archive.zip that may be embedded in the payload
            let embeddedFiles = null;
            try {
                const innerZip = await JSZip.loadAsync(payloadBuffer);
                const fileObjs = Object.values(innerZip.files).filter((f) => !f.dir);
                embeddedFiles = await Promise.all(
                    fileObjs.map(async (f) => {
                        const size = (await f.async("arraybuffer")).byteLength;
                        return {name: f.name, size};
                    })
                );
            } catch (_) {
                // not a zip
            }

            const tstUrl = URL.createObjectURL(
                new Blob([tstBuffer], {type: "application/timestamped-data"})
            );
            const payloadUrl = URL.createObjectURL(
                new Blob([payloadBuffer], {type: "application/zip"})
            );

            // Parse the TST file
            const asn1Resp = asn1js.fromBER(tstBuffer);
            if (asn1Resp.offset === -1) throw new Error("Impossible de décoder le fichier TST.");
            const cms = new ContentInfo({schema: asn1Resp.result});
            const signedData = new SignedData({schema: cms.content});
            const eContentBuffer = signedData.encapContentInfo?.eContent?.valueBlock?.valueHex;
            if (!eContentBuffer) throw new Error("Le fichier TST ne contient pas de données encapsulées.");
            const tstASN1 = asn1js.fromBER(eContentBuffer);
            const tstInfo = new TSTInfo({schema: tstASN1.result});

            const signerCert = signedData.certificates?.[0];
            if (!signerCert) throw new Error("Le fichier TST ne contient aucun certificat.");

            // Verify the signature
            // TODO: Don't blindly trust the certificates
            // We could store trusted CA certs somewhere and check against them
            const verifyResult = await signedData.verify({
                signer: 0,
                data: payloadBuffer,
                trustedCerts: [signerCert],
                checkChain: false,
                extendedMode: true,
            });
            if (!verifyResult || verifyResult.signatureVerified !== true)
                throw new Error("La vérification de l'horodatage a échoué.");

            // Build the certificates chain
            const certsChain = (signedData.certificates || []).map((c, i) => ({
                idx: i + 1,
                subjectCN: getCN(c.subject),
                issuerCN: getCN(c.issuer),
                serial: toHex(c.serialNumber.valueBlock.valueHex),
                notBefore: c.notBefore.value.toLocaleDateString(),
                notAfter: c.notAfter.value.toLocaleDateString(),
            }));

            const imprintAlgOID = tstInfo.messageImprint.hashAlgorithm.algorithmId;
            const imprintAlg = HASH_OID_TO_NAME[imprintAlgOID] || imprintAlgOID;
            const imprintHash = toHex(
                tstInfo.messageImprint.hashedMessage.valueBlock.valueHex
            );


            // TSA data from TSTInfo with a fallback to signer cert subject for CN as it may not be present
            const tsaDir = parseGeneralNameDirectory(tstInfo.tsa);
            const tsaData = {
                cn: tsaDir.cn || getAttr(signerCert.subject, "2.5.4.3"),
                o: tsaDir.o,
                ou: tsaDir.ou,
                country: tsaDir.country,
                state: tsaDir.state,
                locality: tsaDir.locality,
                serial: certsChain.at(-1).serial,
                validFrom: certsChain.at(-1).notBefore,
                validTo: certsChain.at(-1).notAfter,
            };


            const utcStr = tstInfo.genTime.toISOString().replace(".000Z", "Z");

            let dtOptions = {
                year: "numeric",
                month: "long",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
            };
            const localStr = new Intl.DateTimeFormat(undefined, dtOptions).format(tstInfo.genTime);

            setDetails({
                file: {name: file.name, size: file.size},
                payload: {name: payloadName, size: payloadBuffer.byteLength, url: payloadUrl},
                embeddedFiles, // may be null
                tst: {
                    size: tstBuffer.byteLength,
                    genTime: tstInfo.genTime,
                    url: tstUrl,
                    imprintAlg,
                    imprintHash,
                    localStr,
                    utcStr,
                },
                tsa: tsaData,
                certificates: certsChain,
            });
            console.log("certsChain:", certsChain)
            setStatus("valid");
        } catch (err) {
            console.error("Verification failed:", err);
            setError(err.message || String(err));
            setStatus("invalid");
        } finally {
            setLoading(false);
        }
    };

    const onDrop = useCallback((acceptedFiles) => {
        const file = acceptedFiles?.[0];
        if (!file) return;

        reset();
        void verifyFile(file); // Start async verification
    }, []);

    const {getRootProps, getInputProps, isDragActive, acceptedFiles} = useDropzone({
        accept: {
            "application/zip": [
                ".asice",
                ".sce",
                ".asics",
                ".scs",
                ".zip"
            ]
        },
        multiple: false,
        onDrop
    });

    return (
        <div className="container">
            {/* File Upload Section */}
            <div className="row justify-content-center">
                <div className="col-lg-8 mb-4">
                    <div className="card">
                        <div className="card-header py-3">
                            <div className="mb-0 d-flex align-items-center fs-6 fw-light">
                                <i className="bi bi-file-earmark-zip me-2"></i>
                                Fichier à vérifier
                            </div>
                        </div>
                        <div className="card-body p-4">
                            <div
                                {...getRootProps()}
                                className={classNames(
                                    "upload-zone p-4 text-center rounded",
                                    {
                                        "bg-light": isDragActive,
                                        "border-light-subtle": isDragActive,
                                        "border-2": isDragActive
                                    }
                                )}
                                style={{cursor: "pointer"}}
                            >
                                {/* Hidden input that triggers the native file picker */}
                                <input {...getInputProps()} />

                                <div className="mb-4">
                                    <i
                                        className="bi bi-file-earmark-arrow-up text-muted"
                                        style={{fontSize: "2rem"}}
                                    ></i>
                                </div>

                                <div className="mb-4">
                                    <p className="form-label fw-light mb-0 fs-5">
                                        {isDragActive
                                            ? (<span>Déposez votre fichier ici</span>)
                                            : (<span>Glissez-déposez un fichier ASiC <small>ou</small>  cliquez pour sélectionner</span>)}
                                    </p>
                                    {acceptedFiles.length > 0 && (<div className="mt-2">
                                        <span>Fichier: </span>
                                        <strong className="text-success">
                                            {acceptedFiles[0].name}
                                        </strong>
                                    </div>)}
                                </div>

                                <div className="text-muted fw-light">
                                    <i className="bi bi-shield-lock me-1"></i>
                                    Les fichiers sont traités localement dans votre navigateur
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Loading */}
            {loading && (
                <div className="row justify-content-center">
                    <div className="col-lg-12 mb-4">
                        <div className="d-flex align-items-center justify-content-center text-muted">
                            <div className="spinner-border spinner-border-sm me-3" role="status">
                                <span className="visually-hidden">Chargement...</span>
                            </div>
                            <div className="text-center">
                                <strong>Traitement en cours...</strong>
                                <div className="small opacity-75">Vérification de l'horodatage</div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Error */}
            {status === "invalid" && (
                <CheckStatus status="invalid">
                    <div>
                        La vérification du fichier a échoué.
                        <div className="small opacity-75 mt-1">{error}</div>
                    </div>
                </CheckStatus>
            )}

            {/* Success */}
            {status === "valid" && details && (<>
                    <div className="row justify-content-center">
                        <div className="col-12 mb-4">
                            <CheckStatus status="valid" details={details} error={error}>
                                <div>
                                    Le document est valide et a été horodaté en date du <strong
                                    className="fs-5 d-inline-block">{details?.tst.localStr}</strong>
                                    <div className="small opacity-75 mt-1">
                                        L'authenticité et l'intégrité du document ont été confirmées
                                    </div>
                                </div>
                            </CheckStatus>
                        </div>
                    </div>

                    {/* TSA Information and Timestamp Token */}
                    <div className="row">
                        <div className="col-xl-7 mb-4">
                            {/* TSA Information */}
                            <div className="card h-100">
                                <div className="card-header bg-secondary text-white section-header py-3">
                                    <div className="mb-0 d-flex align-items-center fs-6 fw-light">
                                        <i className="bi bi-building me-2"></i>
                                        Authorité d'horodatage (TSA)
                                    </div>
                                </div>
                                <div className="card-body p-4">
                                    <div className="row mb-3">
                                        <div className="col-sm-3 border-end">
                                            <span className="info-label">Nom commun (CN)</span>
                                        </div>
                                        <div className="col-sm-9">
                                            <span className="info-value">{details.tsa.cn || "—"}</span>
                                        </div>
                                    </div>
                                    {details.tsa.o && (
                                        <div className="row mb-3">
                                            <div className="col-sm-3 border-end">
                                                <span className="info-label">Organisation (O)</span>
                                            </div>
                                            <div className="col-sm-9">
                                                <span className="info-value">{details.tsa.o}</span>
                                            </div>
                                        </div>
                                    )}
                                    {details.tsa.ou && (
                                        <div className="row mb-3">
                                            <div className="col-sm-3 border-end">
                                                <span className="info-label">Unité d'organisation (OU)</span>
                                            </div>
                                            <div className="col-sm-9">
                                                <span className="info-value">{details.tsa.ou}</span>
                                            </div>
                                        </div>
                                    )}
                                    <div className="row mb-3">
                                        <div className="col-sm-3 border-end">
                                            <span className="info-label">Localisation (L)</span>
                                        </div>
                                        <div className="col-sm-9">
                                            <span className="info-value">
                                                {[details.tsa.locality, details.tsa.state, details.tsa.country]
                                                    .filter(Boolean)
                                                    .join(", ")}
                                            </span>
                                        </div>
                                    </div>
                                    <div className="row mb-3">
                                        <div className="col-sm-3 border-end">
                                                    <span
                                                        className="info-label">Numéro de série<br/>du certificat</span>
                                        </div>
                                        <div className="col-sm-9">
                                            <div className="hash-display">
                                                {details.tsa.serial}
                                            </div>
                                        </div>
                                    </div>
                                    <div className="row">
                                        <div className="col-sm-3 border-end">
                                            <span className="info-label">Validité du certificat</span>
                                        </div>
                                        <div className="col-sm-9">
                                            <span className="info-value">
                                                {details.tsa.validFrom} → {details.tsa.validTo}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div className="col-xl-5 mb-4">
                            {/* Timestamp Token */}
                            <div className="card mb-4 h-100">
                                <div className="card-header  bg-secondary text-white section-header py-3">
                                    <div className="mb-0 d-flex align-items-center fs-6 fw-light">
                                        <i className="bi bi-clock me-2"></i>
                                        Jeton d'horodatage
                                    </div>
                                </div>
                                <div className="card-body p-4">
                                    <div className="row mb-3">
                                        <div className="col-sm-3 border-end">
                                            <span className="info-label">Date de création</span>
                                        </div>
                                        <div className="col-sm-9">
                                            <span className="info-value">{details.tst.localStr}</span>
                                        </div>
                                    </div>
                                    <div className="row mb-3">
                                        <div className="col-sm-3 border-end">
                                            <span className="info-label">Algorithme <br/> de hash</span>
                                        </div>
                                        <div className="col-sm-9">
                                            <span className="badge badge-subtle">{details.tst.imprintAlg}</span>
                                        </div>
                                    </div>
                                    <div className="row mb-3">
                                        <div className="col-sm-3 border-end">
                                            <span className="info-label">Hash</span>
                                        </div>
                                        <div className="col-sm-9">
                                            <div className="hash-display">
                                                {details.tst.imprintHash}
                                            </div>
                                        </div>
                                    </div>
                                    <div className="row">
                                        <div className="col-sm-3 border-end">
                                        </div>
                                        <div className="col-sm-9">
                                            <a
                                                href={details.tst.url}
                                                download="timestamp.tst"
                                                className="btn btn-outline-secondary btn-sm"
                                            >
                                                <i className="bi bi-download me-1"/> Télécharger le jeton .tst
                                            </a>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>


                    {/* Certificate Chain */}
                    <div class="row justify-content-center">
                        <div class="col-12 mb-4">
                            <div className="card pb-2">
                                <div className="card-header section-header py-3">
                                    <div className="mb-0 d-flex align-items-center fs-6 fw-light">
                                        <i className="bi bi-award me-2"></i>
                                        Chaîne de certificats
                                    </div>
                                </div>
                                <div className="card-body p-0">
                                    <CertTable certs={details.certificates}/>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* File and Embedded Files Information */}
                    <div className="row justify-content-center">
                        <div className="col-xl-4 mb-4">
                            {/* File Information */}
                            <div className="card h-100 mb-4">
                                <div className="card-header section-header py-3">
                                    <div className="mb-0 d-flex align-items-center small fw-light">
                                        <i className="bi bi-file-text me-2"></i>
                                        Informations du fichier ASiC
                                    </div>
                                </div>
                                <div className="card-body p-4">
                                    <div className="row mb-3">
                                        <div className="col-sm-3 border-end">
                                            <span className="info-label">Nom</span>
                                        </div>
                                        <div className="col-sm-9">
                                            <span className="info-value">{details.file.name}</span>
                                        </div>
                                    </div>
                                    <div className="row">
                                        <div className="col-sm-3 border-end">
                                            <span className="info-label">Taille</span>
                                        </div>
                                        <div className="col-sm-9">
                                            <span className="info-value">{fmtBytes(details.file.size)}</span>
                                        </div>
                                    </div>
                                    <div className="row mt-3">
                                        <div className="col-sm-3 border-end">
                                        </div>
                                        <div className="col-sm-9">
                                            <a
                                                href={details.payload.url}
                                                download={details.payload.name}
                                                className="btn btn-outline-secondary btn-sm"
                                            >
                                                <i className="bi bi-download me-1"/> Télécharger le contenu .zip
                                            </a>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div className="col-xl-8 mb-4">
                            {/* Embedded Files */}
                            {details.embeddedFiles && (
                                <div className="card h-100 pb-2 mb-4">
                                    <div className="card-header section-header py-3">
                                        <div className="mb-0 d-flex align-items-center small fw-light">
                                            <i className="bi bi-folder2-open me-2"></i>
                                            Contenu de l'archive
                                        </div>
                                    </div>
                                    <div className="card-body p-0">
                                        <EmbeddedTable files={details.embeddedFiles}/>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}

export default TimestampCheck;
