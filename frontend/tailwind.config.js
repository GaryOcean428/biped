/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Brand colors from your logo gradient
        brand: {
          coral: '#ff4757',     // Top of gradient
          orange: '#ff7675',    // Orange transition
          yellow: '#fdcb6e',    // Yellow section
          lime: '#6c5ce7',      // Lime green
          cyan: '#00cec9',      // Cyan/teal
          purple: '#a29bfe',    // Purple section
          magenta: '#fd79a8',   // Magenta/pink
        },
        
        // Light theme - warm, soft backgrounds
        light: {
          bg: {
            primary: '#fefefe',    // Very soft off-white
            secondary: '#f8f9fa',  // Light warm gray
            tertiary: '#f1f3f4',   // Slightly darker warm gray
            chat: '#ffffff',       // Chat bubbles
          },
          text: {
            primary: '#2d3436',    // Dark charcoal for main text
            secondary: '#636e72',  // Medium gray for secondary text
            tertiary: '#74b9ff',   // Muted for timestamps/meta
          },
          border: '#e9ecef',       // Subtle borders
        },
        
        // Dark theme - deep navy with vibrant accents
        dark: {
          bg: {
            primary: '#0a0e1a',    // Very dark navy (from your logo bg)
            secondary: '#1a1f2e',  // Slightly lighter navy for cards
            tertiary: '#2c3447',   // Medium navy for hover states
            chat: '#252b3d',       // Chat bubble background
          },
          text: {
            primary: '#f8f9fa',    // Pure white for readability
            secondary: '#adb5bd',  // Light gray for secondary text
            tertiary: '#6c757d',   // Muted gray for timestamps
          },
          border: '#495057',       // Subtle dark borders
          accent: {
            primary: '#00cec9',    // Cyan from logo
            secondary: '#a29bfe',  // Purple from logo
            success: '#00b894',    // Success green
            warning: '#fdcb6e',    // Warning yellow
            danger: '#e17055',     // Danger coral
          }
        },
        
        // Chat-specific colors
        chat: {
          user: {
            light: '#667eea',      // User message bubble (light)
            dark: '#764ba2',       // User message bubble (dark)
          },
          agent: {
            light: '#f093fb',      // Agent message bubble (light) 
            dark: '#4facfe',       // Agent message bubble (dark)
          },
          system: {
            light: '#ffeaa7',      // System message (light)
            dark: '#fdcb6e',       // System message (dark)
          }
        }
      },
      
      backgroundImage: {
        // Subtle grid patterns
        'grid-light': 'url("data:image/svg+xml,%3csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 32 32\' width=\'32\' height=\'32\' fill=\'none\' stroke=\'rgb(0 0 0 / 0.02)\'%3e%3cpath d=\'M0 .5H31.5V32\'/%3e%3c/svg%3e")',
        'grid-dark': 'url("data:image/svg+xml,%3csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 32 32\' width=\'32\' height=\'32\' fill=\'none\' stroke=\'rgb(255 255 255 / 0.03)\'%3e%3cpath d=\'M0 .5H31.5V32\'/%3e%3c/svg%3e")',
        
        // Gradient backgrounds inspired by your logo
        'gradient-brand': 'linear-gradient(135deg, #ff4757 0%, #ff7675 25%, #fdcb6e 50%, #00cec9 75%, #a29bfe 100%)',
        'gradient-chat-user': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'gradient-chat-agent': 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
        'gradient-neural': 'radial-gradient(circle at center, rgba(0, 206, 201, 0.1) 0%, transparent 50%)',
      },
      
      boxShadow: {
        // Chat-specific shadows
        'chat-light': '0 2px 8px rgba(0, 0, 0, 0.08)',
        'chat-dark': '0 4px 12px rgba(0, 0, 0, 0.4)',
        'message-hover': '0 4px 16px rgba(0, 206, 201, 0.2)',
        
        // Neon effects for dark mode
        'neon-cyan': '0 0 10px rgba(0, 206, 201, 0.5)',
        'neon-purple': '0 0 10px rgba(162, 155, 254, 0.5)',
        'neon-coral': '0 0 10px rgba(255, 71, 87, 0.5)',
      },
      
      animation: {
        'typing': 'typing 1.5s infinite',
        'pulse-soft': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      
      keyframes: {
        typing: {
          '0%, 60%': { opacity: '1' },
          '30%': { opacity: '0.4' },
        },
        glow: {
          '0%': { boxShadow: '0 0 5px rgba(0, 206, 201, 0.2)' },
          '100%': { boxShadow: '0 0 20px rgba(0, 206, 201, 0.6)' },
        }
      },
      
      fontFamily: {
        'display': ['Inter', 'system-ui', 'sans-serif'],
        'body': ['Inter', 'system-ui', 'sans-serif'],
        'mono': ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
}