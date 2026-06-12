import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  // Dev-only proxy to the FastAPI backend; not applied to the static export.
  async rewrites() {
    return [{ source: "/api/:path*", destination: "http://localhost:8000/api/:path*" }];
  },
};

export default nextConfig;
