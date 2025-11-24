import js from "@eslint/js";
import globals from "globals";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import tseslint from "typescript-eslint";

export default tseslint.config(
  // Ignore generated files and build artifacts
  { ignores: ["dist/**", ".vite/**", "node_modules/**", "coverage/**"] },

  // Base recommended configs
  js.configs.recommended,
  ...tseslint.configs.recommended,

  // React-specific configuration
  {
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
    plugins: {
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      "react-refresh/only-export-components": [
        "warn",
        { allowConstantExport: true },
      ],
      // Prevent console.log in production code - use logger utility instead
      "no-console": [
        "warn",
        {
          allow: ["warn", "error"], // Allow console.warn and console.error for now
        },
      ],
    },
  },
);
