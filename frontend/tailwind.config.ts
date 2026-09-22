import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        terminal: {
          bg: "#080c14",
          panel: "#0d131f",
          card: "#121929",
          border: "#1e293b",
          borderBright: "#334155",
          text: "#e2e8f0",
          muted: "#94a3b8",
          dim: "#64748b",
        },
        gold: {
          50: "#fffbeb",
          100: "#fef3c7",
          200: "#fde68a",
          300: "#fcd34d",
          400: "#fbbf24",
          500: "#f59e0b",
          600: "#d97706",
          700: "#b45309",
        },
        bull: {
          DEFAULT: "#10b981",
          subtle: "rgba(16, 185, 129, 0.15)",
        },
        bear: {
          DEFAULT: "#f43f5e",
          subtle: "rgba(244, 63, 94, 0.15)",
        },
      },
      fontFamily: {
        mono: [
          "JetBrains Mono",
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Monaco",
          "Consolas",
          "Liberation Mono",
          "Courier New",
          "monospace",
        ],
      },
    },
  },
  plugins: [],
};
export default config;
