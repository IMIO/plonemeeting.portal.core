import { h, render } from "preact";
import { useState } from "preact/hooks";
import Icon from "@mdi/react";
import { mdiPlus, mdiEqual, mdiMinus, mdiPencil } from "@mdi/js";
import ReactTooltip from "react-tooltip";

const Annexe = ({ data, type }) => {
    const id = Math.random();

    const getIcon = () => {
        if (type === "unchanged") return mdiEqual;
        if (type === "added") return mdiPlus;
        if (type === "modified") return mdiPencil;
        if (type === "removed") return mdiMinus;
    };

    return (
        <div className={`annex-status ${type}`} data-tip data-for={`pp${id}`}>
            <Icon path={getIcon()} color="white" />
            <span>{data.count}</span>
            <ReactTooltip id={`pp${id}`} type="dark" place="left" effect="solid">
                <ul>
                    {data.titles.map((title) => (
                        <li key={title}>{title}</li>
                    ))}
                </ul>
            </ReactTooltip>
        </div>
    );
};

const AnnexesStatus = (props) => {
    const annexes = JSON.parse(props["data-annexes"]);

    return (
        <div className="annexes-status">
            {annexes.unchanged && <Annexe data={annexes.unchanged} type="unchanged" />}
            {annexes.removed && <Annexe data={annexes.removed} type="removed" />}
            {annexes.added && <Annexe data={annexes.added} type="added" />}
            {annexes.modified && <Annexe data={annexes.modified} type="modified" />}
        </div>
    );
};

export default AnnexesStatus;
