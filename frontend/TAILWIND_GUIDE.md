# Biped Tailwind CSS Configuration Guide

This guide provides comprehensive documentation for the custom Tailwind CSS configuration implemented for the Biped platform, featuring a vibrant gradient-based color scheme optimized for both light and dark themes.

## Overview

The Biped Tailwind configuration extends the default Tailwind CSS setup with:
- Custom brand colors derived from the Biped logo gradient
- Comprehensive light and dark theme color palettes
- Chat-specific styling for AI interfaces
- Custom animations and effects
- Typography optimized for modern interfaces

## Installation & Setup

### 1. Prerequisites
```bash
npm install -D tailwindcss@^3.0.0 postcss autoprefixer
```

### 2. Configuration Files

**postcss.config.js**
```javascript
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

**tailwind.config.js** - See the main configuration file for complete setup.

### 3. CSS Integration
Add to your main CSS file (e.g., `src/index.css`):
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

## Color Palette

### Brand Colors
Based on the Biped logo gradient:
- `brand-coral`: #ff4757 - Primary brand color
- `brand-orange`: #ff7675 - Secondary accent
- `brand-yellow`: #fdcb6e - Warm highlight
- `brand-lime`: #6c5ce7 - Energy accent
- `brand-cyan`: #00cec9 - Tech primary
- `brand-purple`: #a29bfe - Innovation
- `brand-magenta`: #fd79a8 - Creative accent

### Light Theme Colors
- **Backgrounds**: `light-bg-primary`, `light-bg-secondary`, `light-bg-tertiary`
- **Text**: `light-text-primary`, `light-text-secondary`, `light-text-tertiary`
- **Borders**: `light-border`

### Dark Theme Colors
- **Backgrounds**: `dark-bg-primary`, `dark-bg-secondary`, `dark-bg-tertiary`
- **Text**: `dark-text-primary`, `dark-text-secondary`, `dark-text-tertiary`
- **Accents**: `dark-accent-primary`, `dark-accent-secondary`, `dark-accent-success`

## Usage Examples

### 1. Main App Layout
```jsx
<div className="bg-light-bg-primary dark:bg-dark-bg-primary bg-grid-light dark:bg-grid-dark min-h-screen transition-colors duration-300">
  {/* Your app content */}
</div>
```

### 2. Chat Container
```jsx
<div className="bg-light-bg-secondary dark:bg-dark-bg-secondary rounded-xl shadow-chat-light dark:shadow-chat-dark">
  {/* Chat messages go here */}
</div>
```

### 3. Message Bubbles

**User Messages (right-aligned)**
```jsx
<div className="ml-auto max-w-xs lg:max-w-md">
  <div className="bg-gradient-chat-user text-white rounded-2xl rounded-br-md px-4 py-2 shadow-chat-light dark:shadow-chat-dark">
    <p className="text-sm">{userMessage}</p>
  </div>
</div>
```

**Agent/AI Messages (left-aligned)**
```jsx
<div className="mr-auto max-w-xs lg:max-w-md">
  <div className="bg-light-bg-chat dark:bg-dark-bg-chat border border-light-border dark:border-dark-border rounded-2xl rounded-bl-md px-4 py-2 shadow-chat-light dark:shadow-chat-dark hover:shadow-message-hover transition-shadow">
    <p className="text-light-text-primary dark:text-dark-text-primary text-sm">{agentMessage}</p>
  </div>
</div>
```

**System Messages (centered)**
```jsx
<div className="mx-auto max-w-xs">
  <div className="bg-chat-system-light dark:bg-chat-system-dark text-light-text-secondary dark:text-dark-text-secondary rounded-full px-3 py-1 text-xs text-center">
    {systemMessage}
  </div>
</div>
```

### 4. Input Area
```jsx
<div className="bg-light-bg-tertiary dark:bg-dark-bg-tertiary border-t border-light-border dark:border-dark-border p-4">
  <div className="flex items-center space-x-3">
    <input 
      type="text"
      placeholder="Type your message..."
      className="flex-1 bg-light-bg-primary dark:bg-dark-bg-secondary text-light-text-primary dark:text-dark-text-primary placeholder-light-text-tertiary dark:placeholder-dark-text-tertiary border border-light-border dark:border-dark-border rounded-lg px-4 py-2 focus:ring-2 focus:ring-dark-accent-primary dark:focus:ring-dark-accent-primary focus:border-transparent transition-all"
    />
    <button className="bg-gradient-brand text-white p-2 rounded-lg hover:shadow-neon-cyan transition-all duration-300">
      <SendIcon className="w-5 h-5" />
    </button>
  </div>
</div>
```

### 5. Navigation/Sidebar
```jsx
<nav className="bg-light-bg-secondary dark:bg-dark-bg-secondary border-r border-light-border dark:border-dark-border w-64 h-full">
  <div className="p-4">
    {/* Logo area with gradient text */}
    <h1 className="text-2xl font-display font-bold bg-gradient-brand bg-clip-text text-transparent">
      Biped
    </h1>
  </div>
  
  {/* Navigation items */}
  <div className="space-y-2 px-4">
    <button className="w-full text-left px-3 py-2 rounded-lg text-light-text-primary dark:text-dark-text-primary hover:bg-light-bg-tertiary dark:hover:bg-dark-bg-tertiary transition-colors">
      New Chat
    </button>
  </div>
</nav>
```

### 6. Buttons and Interactive Elements

**Primary Action Button**
```jsx
<button className="bg-gradient-brand text-white px-6 py-2 rounded-lg hover:shadow-neon-cyan transition-all duration-300 font-medium">
  Send Message
</button>
```

**Secondary Button**
```jsx
<button className="bg-light-bg-tertiary dark:bg-dark-bg-tertiary text-light-text-primary dark:text-dark-text-primary border border-light-border dark:border-dark-border px-4 py-2 rounded-lg hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary transition-colors">
  Clear Chat
</button>
```

**Icon Button with Glow Effect**
```jsx
<button className="p-2 rounded-lg bg-dark-accent-primary text-white hover:animate-glow transition-all">
  <Icon className="w-5 h-5" />
</button>
```

### 7. Status Indicators

**Typing Indicator**
```jsx
<div className="flex items-center space-x-2 text-light-text-tertiary dark:text-dark-text-tertiary">
  <div className="flex space-x-1">
    <div className="w-2 h-2 bg-dark-accent-primary rounded-full animate-typing"></div>
    <div className="w-2 h-2 bg-dark-accent-primary rounded-full animate-typing" style={{animationDelay: '0.2s'}}></div>
    <div className="w-2 h-2 bg-dark-accent-primary rounded-full animate-typing" style={{animationDelay: '0.4s'}}></div>
  </div>
  <span className="text-xs">AI is thinking...</span>
</div>
```

**Online Status**
```jsx
<div className="flex items-center space-x-2">
  <div className="w-3 h-3 bg-dark-accent-success rounded-full animate-pulse-soft"></div>
  <span className="text-xs text-light-text-tertiary dark:text-dark-text-tertiary">Connected</span>
</div>
```

### 8. Theme Toggle
```jsx
<button 
  onClick={toggleTheme}
  className="p-2 rounded-lg bg-light-bg-tertiary dark:bg-dark-bg-tertiary hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary transition-colors"
>
  {isDark ? 
    <SunIcon className="w-5 h-5 text-brand-yellow" /> : 
    <MoonIcon className="w-5 h-5 text-dark-accent-primary" />
  }
</button>
```

## Custom Gradients

The configuration includes several custom gradient backgrounds:

- `bg-gradient-brand` - Full logo gradient
- `bg-gradient-chat-user` - User message gradient
- `bg-gradient-chat-agent` - Agent message gradient
- `bg-gradient-neural` - Subtle radial gradient for backgrounds

## Animations

### Built-in Animations
- `animate-typing` - Dots animation for typing indicators
- `animate-pulse-soft` - Gentle pulse for status indicators
- `animate-glow` - Glowing effect for interactive elements

### Usage
```jsx
<div className="animate-typing">...</div>
<div className="animate-pulse-soft">...</div>
<div className="hover:animate-glow">...</div>
```

## Typography

### Font Families
- `font-display` - Inter for headings and display text
- `font-body` - Inter for body text
- `font-mono` - JetBrains Mono for code and monospace

### Usage
```jsx
<h1 className="font-display font-bold">Heading Text</h1>
<p className="font-body">Body text content</p>
<code className="font-mono">Code snippet</code>
```

## Dark Mode Implementation

### Setup
1. Add `darkMode: 'class'` to your Tailwind config
2. Use the `dark:` prefix for dark mode styles
3. Toggle the `dark` class on your root element

### Example Implementation
```jsx
const [isDark, setIsDark] = useState(false);

const toggleTheme = () => {
  setIsDark(!isDark);
  document.documentElement.classList.toggle('dark');
};

return (
  <div className={isDark ? 'dark' : ''}>
    {/* Your content with dark: prefixed classes */}
  </div>
);
```

## Best Practices

1. **Consistent Color Usage**: Always use the defined color palette rather than arbitrary colors
2. **Theme Support**: Include both light and dark variants for all interactive elements
3. **Transitions**: Add smooth transitions for better user experience
4. **Accessibility**: Ensure proper contrast ratios in both themes
5. **Performance**: Use the appropriate shadows and effects sparingly

## Demo Component

See `src/components/BipedChatDemo.js` for a comprehensive example implementation showcasing all the features of the Biped Tailwind configuration.

## Browser Support

This configuration requires:
- Modern browsers that support CSS custom properties
- Tailwind CSS v3.0+
- PostCSS processing

The implementation provides excellent browser compatibility while maintaining modern design features.