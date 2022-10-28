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
    control: (provided, state) => {
        if (state.isFocused) {
            return {
                ...provided,
                border: 0,
                outline: 0,
                boxShadow: "0 0 0 3px #f1f1f180",
            };
        }
        return {
            ...provided,
            border: "0",
        };
    },
};
