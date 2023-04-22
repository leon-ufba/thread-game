/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,ts}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          "Poppins", "ui-sans-serif", "system-ui", "-apple-system",
          "BlinkMacSystemFont", "Segoe UI", "Roboto", "Helvetica Neue",
          "Arial", "Noto Sans", "sans-serif", "Apple Color Emoji",
          "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji",
        ],
        'icon': ['Material Icons'],
      },
    },
  },
  plugins: [],
}
