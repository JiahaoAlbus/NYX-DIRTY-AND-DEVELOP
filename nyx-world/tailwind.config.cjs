module.exports = {
  darkMode: 'class',
  content: [
    "./index.html",
    "./App.tsx",
    "./index.tsx",
    "./components/**/*.{ts,tsx,js,jsx}",
    "./screens/**/*.{ts,tsx,js,jsx}",
    "./*.{ts,tsx,js,jsx}"
  ],
  theme: {
    extend: {
      colors: {
        primary: "#F0B90B", // Binance Yellow
        "primary-dark": "#D4A300",
        "background-light": "#FAFAFA",
        "background-dark": "#0B0E11", // Binance Dark
        "card-light": "rgba(255, 255, 255, 0.7)",
        "card-dark": "rgba(30, 32, 38, 0.7)", // Binance Card Dark
        "surface-light": "#EAECEF",
        "surface-dark": "#1E2329",
        "text-main": "#1E2329",
        "text-subtle": "#707A8A",
        "binance-green": "#0ECB81",
        "binance-red": "#F6465D",
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
    fontFamily: {
      display: ["system-ui", "sans-serif"],
    },
  },
  plugins: [],
};
