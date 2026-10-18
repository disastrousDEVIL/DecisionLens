import { FlatCompat } from "@eslint/eslintrc";
import { globalIgnores } from "eslint/config";

const compat = new FlatCompat({ baseDirectory: import.meta.dirname });
const nextConfig = compat.extends("next/core-web-vitals");

const config = [globalIgnores([".next/**"]), ...nextConfig];

export default config;
