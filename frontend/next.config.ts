import type { NextConfig } from "next";

/**
 * Configuration minimale du frontend public (Phase 9a).
 *
 * Aucune URL d'API ni aucun secret ici : l'adresse de l'API publique vient de
 * `NEXT_PUBLIC_API_BASE_URL` au moment du build (variables `NEXT_PUBLIC_*`
 * inlinées par Next), et le client échoue proprement si elle manque
 * (`frontend/lib/api.ts`).
 */
const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
};

export default nextConfig;
