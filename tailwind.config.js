/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        borderMuted: '#333333',
        accentGold: '#d4af37'
      }
    },
  },
  plugins: [],
}
