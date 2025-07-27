// tailwind.config.js
module.exports = {
  content: [
    './templates/**/*.html',
    // Add any other paths where you use Tailwind/DaisyUI classes
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        display: ['Playfair Display', 'serif'],
      },
      // You can define custom colors here if they are not part of DaisyUI's theme
      // For instance, if you want a specific "brand-black" not mapped to 'neutral'
      colors: {
        'brand-dark': '#1A1A1A', // A very deep charcoal/off-black
        'brand-yellow': '#FFD700', // A vibrant gold/yellow
        'brand-light-gray': '#F8F8F8', // A very light, almost white gray
      }
    },
  },
  plugins: [require('daisyui')],
  daisyui: {
    themes: [
      {
        chaze_fashion_dark_yellow: { // A NEW, DISTINCT THEME NAME for this palette
          "primary": "#FFD700",          // Vibrant Yellow for primary actions & hovers (brand-yellow)
          "secondary": "#B0C4DE",        // A muted blue-grey for secondary accents
          "accent": "#FFA07A",           // Light Salmon for additional pop (if needed)

          "neutral": "#1A1A1A",          // Very dark charcoal/off-black for navbar text, main buttons (brand-dark)
          "neutral-content": "#FFFFFF",  // White text on neutral background

          "base-100": "#FFFFFF",         // Pure white for main content background
          "base-200": "#F5F5F5",         // Slightly off-white for footer/alternate sections
          "base-300": "#E0E0E0",         // Light gray for borders/dividers

          "base-content": "#333333",     // Dark gray for general text on light backgrounds

          "info": "#64B5F6",
          "success": "#66BB6A",
          "warning": "#FFCA28",
          "error": "#EF5350",

          "primary-content": "#333333",  // Text on primary (yellow) elements - make it dark for contrast
          "secondary-content": "#333333",// Text on secondary (blue-grey) elements
          "accent-content": "#333333",   // Text on accent (salmon) elements
        },
      },
      // You can keep 'light' here as a fallback if 'chaze_fashion_dark_yellow' is not applied
      "light",
    ],
  },
};
