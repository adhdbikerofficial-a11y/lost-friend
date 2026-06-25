const { getDefaultConfig } = require("expo/metro-config");

const config = getDefaultConfig(__dirname);

// Disable Hermes bytecode in development — it's extremely slow
// and causes "Failed to download remote update" on physical devices.
config.transformer.minifierConfig = {
  ...config.transformer.minifierConfig,
  bytecode: false,
};

module.exports = config;
