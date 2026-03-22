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
        panel: "0 10px 30px rgba(18, 18, 18, 0.06)",
      },
      fontFamily: {
        sans: ["Avenir Next", "Helvetica Neue", "sans-serif"],
      },
      keyframes: {
        rise: {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        rise: "rise 360ms cubic-bezier(0.2, 0.8, 0.2, 1) both",
      },
    },
  },
  plugins: [],
};
