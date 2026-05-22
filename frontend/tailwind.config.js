/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        kaznu: {
          DEFAULT: '#003F87',
          dark: '#002d63',
          light: '#1a56db',
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          900: '#001a4d',
        },
      },
      boxShadow: {
        'card': '0 4px 24px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.06)',
        'card-hover': '0 8px 32px rgba(0,63,135,0.4), 0 0 0 1px rgba(99,179,237,0.2)',
        'glow-blue': '0 0 20px rgba(59,130,246,0.4)',
        'glow-green': '0 0 16px rgba(34,197,94,0.4)',
      },
      animation: {
        'fade-up': 'fadeUp 0.5s ease-out',
        'fade-in': 'fadeIn 0.4s ease-out',
        'pulse2': 'pulse2 2s ease-in-out infinite',
        'slide-left': 'slideLeft 0.4s ease-out',
        'counter': 'counter 0.6s ease-out',
      },
      keyframes: {
        fadeUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideLeft: {
          '0%': { opacity: '0', transform: 'translateX(20px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        pulse2: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.4' },
        },
        counter: {
          '0%': { transform: 'scale(1.2)', opacity: '0.7' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
      },
      backgroundImage: {
        'gradient-kaznu': 'linear-gradient(135deg, #003F87 0%, #1a56db 100%)',
        'gradient-dark': 'linear-gradient(135deg, #020c1e 0%, #040d1f 100%)',
      },
    },
  },
  plugins: [],
}
