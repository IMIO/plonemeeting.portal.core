import {Tooltip} from "react-tooltip";

const PmTooltip = ({targetSelector, content, position}) => {
    return (
        <Tooltip className="pm-tooltip" variant="light" anchorSelect={targetSelector} place={position} opacity={1} offset={15}>
            {content}
        </Tooltip>
    )
};

export default PmTooltip;
