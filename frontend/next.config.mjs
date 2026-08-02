/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  // Proxies the browser's API calls through this same Next.js server
  // instead of requiring the browser to reach the backend on its own
  // port directly. `NEXT_PUBLIC_API_URL=http://localhost:8000` only
  // works when the browser's "localhost" is literally the same machine
  // Docker runs on (true for a bare host browser, confirmed live) — it
  // breaks the instant the app is reached through anything that
  // forwards port 3000 without also forwarding 8000 (a VSCode/remote
  // port-forward, a tunnel, etc.), surfacing as "Failed to fetch" on
  // every API call including Create Organization (confirmed live: this
  // is exactly what a real user hit while port 3000 worked fine). This
  // rewrite runs server-side, inside the same Docker network as
  // `backend`, so `backend:8000` always resolves regardless of how the
  // browser reached this page — the browser only ever talks to its own
  // origin.
  async rewrites() {
    return [{ source: "/api/:path*", destination: "http://backend:8000/:path*" }];
  },
};

export default nextConfig;
