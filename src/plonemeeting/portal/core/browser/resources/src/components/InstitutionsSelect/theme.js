export const theme = (originalTheme) => ({
    ...originalTheme,
    colors: {
        ...originalTheme.colors,
        primary75: "#f1f1f1",
        primary50: "#DE007B21",
        primary25: "#f1f1f1",
        primary: "#DE007B",
    },
});

export const style = {
    control: (provided, state) => ({
        ...provided,
        border: "0",
    }),
};
