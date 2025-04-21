/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html", // Adjust based on your file structure
    "./static/**/*.js",      // Include any custom JS files if needed
  ],
  theme: {
    extend: {
      fontFamily: {
        playfair: ['"Playfair Display"', 'serif'], // Ensure quotes and syntax are correct
      },
    },
  },
  plugins: [
    require('tailwind-scrollbar')
  ],
};


