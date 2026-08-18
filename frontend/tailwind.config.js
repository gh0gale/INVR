/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      /*
        Archivo is a grotesque with a genuine point of view and a weight range
        that holds up at display sizes, which is what the headings needed.
        JetBrains Mono carries every figure: it was drawn for dense numeric
        reading, so prices and tickers stay legible small. Newsreader is kept
        for the legal documents, a deliberately different register.
        None of the three is Inter, Geist or Space Grotesk.
      */
      /*
        One family, everywhere. Archivo carries headings, body, labels and
        figures alike; a second face for numerals was reading as a mismatch
        against the ticker and verdict type. Alignment in numeric columns now
        comes from `tabular-nums` (the `.num` class) rather than from a
        monospace font. `mono` and `display` are aliased to the same stack so
        any stray utility renders identically instead of falling back.
      */
      fontFamily: {
        sans: ['Archivo', 'Segoe UI', 'system-ui', 'sans-serif'],
        mono: ['Archivo', 'Segoe UI', 'system-ui', 'sans-serif'],
        display: ['Archivo', 'Segoe UI', 'system-ui', 'sans-serif'],
      },

      /*
        Type scale, raised across the board. The old scale bottomed out at 10px
        for labels and 14px for body, which was too small to read comfortably.
        Body now sits at 17px and the smallest label is 12px.
      */
      fontSize: {
        '2xs': ['0.75rem', { lineHeight: '1.05rem', letterSpacing: '0.01em' }], // 12
        xs: ['0.8125rem', { lineHeight: '1.2rem' }], // 13
        sm: ['0.9375rem', { lineHeight: '1.5rem' }], // 15
        base: ['1.0625rem', { lineHeight: '1.7rem' }], // 17
        lg: ['1.1875rem', { lineHeight: '1.85rem' }], // 19
        xl: ['1.375rem', { lineHeight: '1.95rem' }], // 22
        '2xl': ['1.75rem', { lineHeight: '2.2rem', letterSpacing: '-0.01em' }], // 28
        '3xl': ['2.25rem', { lineHeight: '2.6rem', letterSpacing: '-0.02em' }], // 36
        '4xl': ['2.875rem', { lineHeight: '3.1rem', letterSpacing: '-0.025em' }], // 46
        '5xl': ['3.75rem', { lineHeight: '3.9rem', letterSpacing: '-0.03em' }], // 60
        '6xl': ['4.75rem', { lineHeight: '4.85rem', letterSpacing: '-0.035em' }], // 76
        '7xl': ['6rem', { lineHeight: '6rem', letterSpacing: '-0.04em' }], // 96
      },

      colors: {
        /*
          Trading terminal. Charcoal ground rather than pure black, so hairlines
          read without glowing. The accent is the amber of a market terminal,
          held at a muted ochre so it never becomes a neon signal colour, and
          there is no violet anywhere near this palette.
        */
        term: {
          950: '#0F1114', // page ground
          900: '#15181D', // raised panel
          850: '#1B1F25', // sunk panel, table stripe
          800: '#23282F', // hover, pressed
        },
        rule: {
          DEFAULT: '#2B323A',
          strong: '#414A55',
        },
        fg: {
          DEFAULT: '#EDEAE2', // warm off-white, never #FFF
          2: '#A8AEB6',
          3: '#79818A',
        },
        accent: '#E0A94A', // terminal amber: labels, keylines, brand
        up: '#59A878',
        down: '#CC5F49',
        note: '#6699B8',
      },
      letterSpacing: {
        label: '0.12em',
      },
    },
  },
  plugins: [],
}
