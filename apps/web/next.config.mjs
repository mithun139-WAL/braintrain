/** @type {import('next').NextConfig} */

// ─── Build-time env var guard ─────────────────────────────────────────────────
// NEXT_PUBLIC_ vars are baked into the client bundle at build time.
// If this variable is missing during a production build (e.g. Vercel), the app
// silently falls back to localhost:8000 and all API calls fail in production.
// Fail fast here so the problem is obvious in CI/CD build logs.
if (process.env.NODE_ENV === "production") {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;
    if (!apiUrl) {
        throw new Error(
            "[next.config] NEXT_PUBLIC_API_URL is not set. " +
            "Add it in your deployment platform (Vercel → Settings → Environment Variables) " +
            "and redeploy. Without it every API call will hit http://localhost:8000."
        );
    }
    if (apiUrl.includes("localhost")) {
        console.warn(
            "[next.config] WARNING: NEXT_PUBLIC_API_URL is set to a localhost URL in a " +
            "production build. This will break in a deployed environment."
        );
    }
}

const nextConfig = {
    transpilePackages: ["@braintrain/shared"],
};

export default nextConfig;
