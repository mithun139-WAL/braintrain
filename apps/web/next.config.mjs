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
            "and redeploy."
        );
    }
    if (/localhost|127\.0\.0\.1/.test(apiUrl)) {
        throw new Error(
            "[next.config] NEXT_PUBLIC_API_URL points to a local address in a production build."
        );
    }
}

const nextConfig = {
    transpilePackages: ["@braintrain/shared"],
};

export default nextConfig;
