import type { NextConfig } from "next";

const config: NextConfig = {
  reactStrictMode: true,
  // standalone server for the Docker image (web/Dockerfile); `next start` serves the plain build
  output: process.env.S2S_STANDALONE ? "standalone" : undefined,
};

export default config;
