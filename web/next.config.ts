import type { NextConfig } from "next";
const config: NextConfig = {
  poweredByHeader: false,
  devIndicators: false,
  // Development edge only. Production Caddy routes /api directly to FastAPI.
  async rewrites() {
    return [
      {
        source: "/uploads/:path*",
        destination: `${process.env.API_URL || "http://127.0.0.1:8000"}/uploads/:path*`,
      },
      {
        source: "/api/:path*",
        destination: `${process.env.API_URL || "http://127.0.0.1:8000"}/api/:path*`,
      },
    ];
  },
};
export default config;
