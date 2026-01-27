module.exports = {
  content: [
    "./index.html",
    "./App.tsx",
    "./index.tsx",
    "./components/**/*.{ts,tsx,js,jsx}",
    "./screens/**/*.{ts,tsx,js,jsx}",
    "./*.{ts,tsx,js,jsx}"
  ],
  theme: {
    extend: {},
    colors: {
      primary: "#e6d3a3",
      "primary-dark": "#d4c192",
      "background-light": "#f8f7f6",
      "background-warm": "#F9F9F7",
      "background-dark": "#1f1c13",
      "card-light": "#FFFEFA",
      "card-dark": "#2a261b",
      "surface-light": "#f1efe9",
      "surface-dark": "#2c2921",
      "text-main": "#191610",
      "text-subtle": "#8d7e58",
    },
    fontFamily: {
      display: ["system-ui", "sans-serif"],
    },
    boxShadow: {
      soft: "0 8px 30px rgba(230, 211, 163, 0.15)",
      "inner-gold": "inset 0 0 0 1px rgba(230, 211, 163, 0.3)",
    },
    animation: {
      "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      shimmer: "shimmer 1.5s infinite",
    },
    keyframes: {
      shimmer: {
        "100%": { transform: "translateX(100%)" },
      },
    },
  },
  plugins: [],
};
