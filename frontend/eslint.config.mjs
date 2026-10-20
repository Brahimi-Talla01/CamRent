import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

/**
 * Lint du frontend : règles Next.js (cœur web vitals) + TypeScript.
 *
 * Les artefacts de build et le typage généré par Next sont ignorés : ce ne sont
 * pas des sources, et les linter ferait échouer la CI sur du code généré
 * (AGENTS.md §3).
 */
export default defineConfig([
  ...nextVitals,
  ...nextTs,
  globalIgnores([".next/**", "out/**", "build/**", "coverage/**", "next-env.d.ts"]),
]);
