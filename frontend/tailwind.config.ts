import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        surface: "#FFFFFF",
        card: "#F8FAFC",
        line: "#E2E8F0",
        ink: "#0F172A",
        muted: "#475569",
        accent: "#1D4ED8",
        emerald: { DEFAULT: "#059669" },
        amber: { DEFAULT: "#D97706" },
        slateBadge: "#64748B",
        rose: { DEFAULT: "#E11D48" },
        roseDeep: "#9F1239",
      },
      fontFamily: {
        sans: ["var(--font-geist-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-geist-mono)", "monospace"],
      },
    },
  },
  plugins: [],
};
export default config;
