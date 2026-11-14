/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './resources/**/*.blade.php',
    './resources/**/*.js',
    './resources/**/*.vue',
  ],
  theme: {
    extend: {
      colors: {
        mantota: {
          teal: '#0BBFA0',
          'teal-dark': '#07856F',
          'teal-pale': '#E6F7F4',
          coral: '#FF6B35',
          whatsapp: '#25D366',
        },
        surface: {
          1: '#F8F9FA',
          2: '#F1F3F5',
          3: '#E9ECEF',
          4: '#DEE2E6',
        },
        grey: {
          1: '#212529',
          2: '#6C757D',
          3: '#495057',
          4: '#868E96',
        },
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'Figtree', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        'mantota': '12px',
        'mantota-card': '14px',
      },
      boxShadow: {
        'mantota': '0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)',
        'mantota-md': '0 4px 12px rgba(0,0,0,0.08)',
        'mantota-lg': '0 8px 24px rgba(0,0,0,0.10)',
        'teal': '0 4px 14px rgba(11,191,160,0.25)',
      },
      animation: {
        'fade-in': 'fadeIn 0.4s ease-out',
        'slide-up': 'slideUp 0.5s cubic-bezier(0.16,1,0.3,1)',
        'float': 'float 6s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-12px)' },
        },
      },
    },
  },
  plugins: [],
};
