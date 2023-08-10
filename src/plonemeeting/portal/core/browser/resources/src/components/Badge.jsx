const StateToColor = {
    published: "green",
    private: "red",
};

const StatusToColor = {
    removed: "red",
    modified: "orange",
};

const Badge = ({ color, children }) => {
    return <div className={`badge ${color}`}>{children}</div>;
};

const StateBadge = ({ state, children }) => {
    return <Badge color={StateToColor[state]}>{children}</Badge>;
};

export { StateToColor, StatusToColor, StateBadge, Badge as default };
