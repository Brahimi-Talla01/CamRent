import { defineConfig } from "vitest/config";

/**
 * Tests unitaires du frontend : uniquement des modules TypeScript purs (client
 * API), sans DOM ni navigateur. Les écrans sont vérifiés par `next build` et à
 * la main, pas par un moteur de rendu.
 */
export default defineConfig({
  test: {
    environment: "node",
    include: ["lib/**/*.test.ts"],
  },
});
