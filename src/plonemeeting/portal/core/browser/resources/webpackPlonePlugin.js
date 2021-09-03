const fs = require("fs");
const xml2js = require("xml2js");


class PlonePlugin {
  /*
   * This will update Plone registry.xml to update last_compilation time of the specified bundle
   */

  constructor(options = {}) {
    this.mode = options.mode;
    this.bundlePrefix = options.bundlePrefix;
    this.registryXmlPath = options.registryXmlPath || fs.realpathSync("./../../profiles/default/registry.xml");
    this.options = options.options || {};
  }

  updateRegistry() {
    const parser = new xml2js.Parser();
    const registryXmlPath = this.registryXmlPath;
    const bundlePrefix = this.bundlePrefix;
    fs.readFile(registryXmlPath, function(err, data) {
      parser.parseString(data, function(err, result) {
        let xml = result;
        let lastCompilationIndex;
        let recordIndex;

        xml.registry.records.map((record, i) => {
          if (record["$"].prefix === bundlePrefix) {
            lastCompilationIndex = record.value.findIndex(v => v["$"].key === "last_compilation");
            recordIndex = i;
          }
        });
        xml.registry.records[recordIndex].value[lastCompilationIndex]._ = new Date().toISOString();
        const builder = new xml2js.Builder();
        xml = builder.buildObject(xml);
        fs.writeFile(registryXmlPath, xml, function(err, data) {
          if (err) console.log(err);
          console.log("Plone's registry.xml successfully updated");
        });
      });
    });
  }

  apply(compiler) {
    compiler.hooks.afterEmit.tap("PlonePlugin", (params, callback) => {
      if (this.mode === "production") {
        this.updateRegistry();
      }
    });
  }
}

module.exports = PlonePlugin;
