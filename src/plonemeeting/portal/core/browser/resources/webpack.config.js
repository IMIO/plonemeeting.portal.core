const path = require("path");

const {CleanWebpackPlugin} = require("clean-webpack-plugin");
const PreactRefreshPlugin = require("@prefresh/webpack");
const CopyPlugin = require("copy-webpack-plugin");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const CssMinimizerPlugin = require("css-minimizer-webpack-plugin");
const JsonMinimizerPlugin = require("json-minimizer-webpack-plugin");
const TerserPlugin = require("terser-webpack-plugin");
const BUNDLE_PREFIX = "plone.bundles/plonemeeting.portal.core";
const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin;

module.exports = (env, argv) => {
  const mode = argv.mode ? argv.mode : "development";
  return {
    mode: mode,
    entry: "./src/index.js",
    output: {
      path: path.resolve(__dirname, "../static"),
      filename: "js/core.js",
    },
    plugins: [
      mode === "production" && new CleanWebpackPlugin(),
      // new BundleAnalyzerPlugin(),
      new PreactRefreshPlugin(),
      new CopyPlugin({
        patterns: [{from: "assets", to: "assets"}],
      }),
      new MiniCssExtractPlugin({
        filename: "css/core.css",
      }),
    ].filter(Boolean),
    module: {
      rules: [
        {
          test: /\.(js|mjs|jsx|ts|tsx)$/,
          use: {
            loader: "babel-loader",
            options: {
              presets: ["@babel/preset-env"],
            },
          },
        },
        {
          test: /\.s[ac]ss$/i,
          use: [
            // In production, creates CSS files
            // In development serve CSS through JS 'with style-loader'
            {
              loader:
                mode === "development"
                  ? "style-loader"
                  : MiniCssExtractPlugin.loader,
            },
            // Translates CSS into CommonJS
            {
              loader: "css-loader",
              options: {
                sourceMap: mode === "development",
              },
            },
            // Use postcss to add vendor prefixes and various transforms to the css
            {
              loader: "postcss-loader",
              options: {
                sourceMap: mode === "development",
              },
            },
            {
              loader: "sass-loader",
              options: {
                sourceMap: mode === "development",
              },
            },
          ],
        },
        {
          test: /\.css$/i,
          use: [
            // In production, creates CSS files
            // In development serve CSS through JS 'with style-loader'
            {
              loader:
                mode === "development"
                  ? "style-loader"
                  : MiniCssExtractPlugin.loader,
            },
            // Translates CSS into CommonJS
            {
              loader: "css-loader",
              options: {
                sourceMap: mode === "development",
              },
            },
          ],
        },
        {
          test: /\.svg$/i,
          issuer: /\.(js|mjs|jsx|ts|tsx)$/,
          use: [
            {
              loader: "@svgr/webpack",
            },
          ],
        },
        {
          test: /\.(png|jpg|gif|jpeg|svg)$/i,
          issuer: /\.(sass|scss|less|css)$/i,
          loader: "file-loader",
          options: {
            name: "[name].[ext]",
            outputPath: "assets",
          },
        },
        {
          test: /\.(eot|woff|woff2|ttf)([?]?.*)$/,
          loader: "file-loader",
          options: {
            name: "[name].[ext]",
            outputPath: "assets/fonts",
          },
        },
      ],
    },
    resolve: {
      alias: {
        react: "preact/compat",
        "react-dom/test-utils": "preact/test-utils",
        "react-dom": "preact/compat",
        leaflet$: "leaflet/dist/leaflet",
      },
      extensions: ["", ".js", ".jsx"],
    },
    externals: {
      jquery: "jQuery",
    },
    optimization: {
      usedExports: true,
      minimizer: [
        new CssMinimizerPlugin(),
        new JsonMinimizerPlugin(),
        new TerserPlugin({
          parallel: true,
        }),
      ],
    },
    performance: {
      maxAssetSize: 750 * 1024,
      maxEntrypointSize: 750 * 1024,
    },
    devServer: {
      port: 3001,
      hot: true,
      liveReload: false,
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
        "Access-Control-Allow-Headers": "X-Requested-With, content-type, Authorization",
      },
      client: {
        overlay: {
          errors: false,
          warnings: false,
          runtimeErrors: false,
        },
      },
      // watchFiles: {
      //     paths: ["./../../**/*.pt"], // Watch for .pt file change
      // },
      // Proxy everything to the Plone Backend EXCEPT our bundle as
      // Webpack Dev Server will serve it.
      // proxy: [
      //     {
      //         context: ["/**", `!**/${BUNDLE_NAME}/**`],
      //         target: "http://localhost:8080",
      //     },
      //     {
      //         context: [`**/${BUNDLE_NAME}/**`],
      //         target: "http://localhost:3001",
      //         pathRewrite: function (path) {
      //             path = path.split(BUNDLE_NAME)[1]; // Keep only the path after our bundle name
      //             return path;
      //         },
      //     },
      // ],
    },
  };
};
