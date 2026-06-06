/** @type {import('tailwindcss').Config} */
export default {
  content: ["./frontend/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#171717",
        mist: "#f5f4ef",
        pine: "#1a5d52",
        brass: "#c99641",
        blush: "#b86a73",
        slate: "#6777a7",
      },
      boxShadow: {
        panel: "0 2px 8px rgba(18, 18, 18, 0.06)",
      },
      fontFamily: {
        sans: ["Avenir Next", "Helvetica Neue", "sans-serif"],
      },
    },
  },
  plugins: [],
};
