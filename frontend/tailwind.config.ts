import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        'azul-marino':  '#0F1C2E',
        'azul-medio':   '#1A3A5C',
        'azul-acento':  '#2563EB',
        'azul-claro':   '#EFF6FF',
        'verde-ok':     '#16A34A',
        'verde-bg':     '#DCFCE7',
        'naranja':      '#D97706',
        'naranja-bg':   '#FEF3C7',
        'amarillo':     '#CA8A04',
        'amarillo-bg':  '#FEF9C3',
        'rojo':         '#DC2626',
        'rojo-bg':      '#FEE2E2',
        'rojo-urg':     '#EF4444',
        'azul-info':    '#2563EB',
        'azul-info-bg': '#DBEAFE',
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

export default config
