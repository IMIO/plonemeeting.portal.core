module.exports = {
    locales: ["en", "fr"],
    catalogs: [
        {
            path: "locales/{locale}/messages",
            include: ["src"],
        },
    ],
    fallbackLocales: {
        default: "en",
    },
    sourceLocale: "en",
    format: "po",
};
