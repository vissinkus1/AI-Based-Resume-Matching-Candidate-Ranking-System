/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          ivory: "var(--color-ivory)",
          paper: "var(--color-paper)",
          sage: "var(--color-sage)",
          "sage-deep": "var(--color-sage-deep)",
          "sage-soft": "var(--color-sage-soft)",
          forest: "var(--color-forest)",
          ink: "var(--color-ink)",
          muted: "var(--color-muted)",
          line: "var(--color-line)",
        },
        band: {
          strong: "var(--color-band-strong)",
          good: "var(--color-band-good)",
          partial: "var(--color-band-partial)",
          weak: "var(--color-band-weak)",
        },
      },
      fontFamily: {
        display: ['"Anton"', 'Impact', '"Arial Narrow"', 'sans-serif'],
        serif: ['"Fraunces"', 'Georgia', 'serif'],
        sans: ['"Inter"', 'system-ui', '-apple-system', 'sans-serif'],
      },
      borderRadius: {
        "3xl": "1.5rem",
        "4xl": "2rem",
      },
      letterSpacing: {
        eyebrow: "0.14em",
      },
      boxShadow: {
        soft: "0 2px 10px rgba(30, 42, 32, 0.04)",
        card: "0 4px 20px rgba(30, 42, 32, 0.05)",
      },
    },
  },
  plugins: [],
};
