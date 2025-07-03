import React, { useState } from 'react';

const BipedChatDemo = () => {
  const [isDark, setIsDark] = useState(false);
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'system',
      text: 'Welcome to Biped AI Assistant',
      timestamp: '10:30 AM'
    },
    {
      id: 2,
      type: 'agent',
      text: 'Hello! I\'m here to help you find the perfect tradesperson for your project. What do you need help with today?',
      timestamp: '10:30 AM'
    },
    {
      id: 3,
      type: 'user',
      text: 'I need a plumber for a kitchen renovation project in Sydney',
      timestamp: '10:31 AM'
    },
    {
      id: 4,
      type: 'agent',
      text: 'Great! I can help you find experienced plumbers in Sydney who specialize in kitchen renovations. Let me search our network of verified tradies for you.',
      timestamp: '10:31 AM'
    }
  ]);

  const [inputMessage, setInputMessage] = useState('');

  const toggleTheme = () => {
    setIsDark(!isDark);
  };

  const sendMessage = () => {
    if (inputMessage.trim()) {
      setMessages([...messages, {
        id: messages.length + 1,
        type: 'user',
        text: inputMessage,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);
      setInputMessage('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      sendMessage();
    }
  };

  return (
    <div className={`${isDark ? 'dark' : ''}`}>
      {/* App container with soft background */}
      <div className="bg-light-bg-primary dark:bg-dark-bg-primary bg-grid-light dark:bg-grid-dark min-h-screen transition-colors duration-300">
        <div className="container mx-auto p-4 max-w-4xl">
          
          {/* Header with theme toggle and branding */}
          <header className="mb-6">
            <div className="flex items-center justify-between bg-light-bg-secondary dark:bg-dark-bg-secondary rounded-xl shadow-chat-light dark:shadow-chat-dark p-6">
              <div>
                <h1 className="text-3xl font-display font-bold bg-gradient-brand bg-clip-text text-transparent">
                  Biped Chat Demo
                </h1>
                <p className="text-light-text-secondary dark:text-dark-text-secondary mt-2">
                  Experience our new Tailwind CSS color scheme
                </p>
              </div>
              
              {/* Theme toggle */}
              <button 
                onClick={toggleTheme}
                className="p-3 rounded-lg bg-light-bg-tertiary dark:bg-dark-bg-tertiary hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary transition-colors"
              >
                {isDark ? 
                  <span className="text-brand-yellow text-xl">☀️</span> : 
                  <span className="text-dark-accent-primary text-xl">🌙</span>
                }
              </button>
            </div>
          </header>

          {/* Main chat area */}
          <div className="bg-light-bg-secondary dark:bg-dark-bg-secondary rounded-xl shadow-chat-light dark:shadow-chat-dark overflow-hidden">
            
            {/* Chat messages */}
            <div className="p-6 space-y-4 h-96 overflow-y-auto">
              {messages.map((message) => {
                if (message.type === 'system') {
                  return (
                    <div key={message.id} className="mx-auto max-w-xs">
                      <div className="bg-chat-system-light dark:bg-chat-system-dark text-light-text-secondary dark:text-dark-text-secondary rounded-full px-3 py-1 text-xs text-center">
                        {message.text}
                      </div>
                    </div>
                  );
                }
                
                if (message.type === 'user') {
                  return (
                    <div key={message.id} className="ml-auto max-w-xs lg:max-w-md">
                      <div className="bg-gradient-chat-user text-white rounded-2xl rounded-br-md px-4 py-2 shadow-chat-light dark:shadow-chat-dark">
                        <p className="text-sm">{message.text}</p>
                        <p className="text-xs opacity-75 mt-1">{message.timestamp}</p>
                      </div>
                    </div>
                  );
                }
                
                return (
                  <div key={message.id} className="mr-auto max-w-xs lg:max-w-md">
                    <div className="bg-light-bg-chat dark:bg-dark-bg-chat border border-light-border dark:border-dark-border rounded-2xl rounded-bl-md px-4 py-2 shadow-chat-light dark:shadow-chat-dark hover:shadow-message-hover transition-shadow">
                      <p className="text-light-text-primary dark:text-dark-text-primary text-sm">{message.text}</p>
                      <p className="text-light-text-tertiary dark:text-dark-text-tertiary text-xs mt-1">{message.timestamp}</p>
                    </div>
                  </div>
                );
              })}
              
              {/* Typing indicator */}
              <div className="flex items-center space-x-2 text-light-text-tertiary dark:text-dark-text-tertiary">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-dark-accent-primary rounded-full animate-typing"></div>
                  <div className="w-2 h-2 bg-dark-accent-primary rounded-full animate-typing" style={{animationDelay: '0.2s'}}></div>
                  <div className="w-2 h-2 bg-dark-accent-primary rounded-full animate-typing" style={{animationDelay: '0.4s'}}></div>
                </div>
                <span className="text-xs">AI is thinking...</span>
              </div>
            </div>
            
            {/* Chat input container */}
            <div className="bg-light-bg-tertiary dark:bg-dark-bg-tertiary border-t border-light-border dark:border-dark-border p-4">
              <div className="flex items-center space-x-3">
                <input 
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Type your message..."
                  className="flex-1 bg-light-bg-primary dark:bg-dark-bg-secondary text-light-text-primary dark:text-dark-text-primary placeholder-light-text-tertiary dark:placeholder-dark-text-tertiary border border-light-border dark:border-dark-border rounded-lg px-4 py-2 focus:ring-2 focus:ring-dark-accent-primary dark:focus:ring-dark-accent-primary focus:border-transparent transition-all"
                />
                <button 
                  onClick={sendMessage}
                  className="bg-gradient-brand text-white p-2 rounded-lg hover:shadow-neon-cyan transition-all duration-300"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                </button>
              </div>
            </div>
          </div>

          {/* Color Palette Demo */}
          <div className="mt-8 bg-light-bg-secondary dark:bg-dark-bg-secondary rounded-xl shadow-chat-light dark:shadow-chat-dark p-6">
            <h2 className="text-xl font-display font-bold text-light-text-primary dark:text-dark-text-primary mb-4">
              Biped Color Palette
            </h2>
            
            {/* Brand Colors */}
            <div className="mb-6">
              <h3 className="text-light-text-secondary dark:text-dark-text-secondary font-medium mb-3">Brand Colors</h3>
              <div className="flex flex-wrap gap-3">
                <div className="flex flex-col items-center">
                  <div className="w-12 h-12 bg-brand-coral rounded-lg shadow-sm"></div>
                  <span className="text-xs mt-1 text-light-text-tertiary dark:text-dark-text-tertiary">Coral</span>
                </div>
                <div className="flex flex-col items-center">
                  <div className="w-12 h-12 bg-brand-orange rounded-lg shadow-sm"></div>
                  <span className="text-xs mt-1 text-light-text-tertiary dark:text-dark-text-tertiary">Orange</span>
                </div>
                <div className="flex flex-col items-center">
                  <div className="w-12 h-12 bg-brand-yellow rounded-lg shadow-sm"></div>
                  <span className="text-xs mt-1 text-light-text-tertiary dark:text-dark-text-tertiary">Yellow</span>
                </div>
                <div className="flex flex-col items-center">
                  <div className="w-12 h-12 bg-brand-cyan rounded-lg shadow-sm"></div>
                  <span className="text-xs mt-1 text-light-text-tertiary dark:text-dark-text-tertiary">Cyan</span>
                </div>
                <div className="flex flex-col items-center">
                  <div className="w-12 h-12 bg-brand-purple rounded-lg shadow-sm"></div>
                  <span className="text-xs mt-1 text-light-text-tertiary dark:text-dark-text-tertiary">Purple</span>
                </div>
              </div>
            </div>

            {/* Action Buttons Demo */}
            <div className="space-y-4">
              <h3 className="text-light-text-secondary dark:text-dark-text-secondary font-medium">Interactive Elements</h3>
              <div className="flex flex-wrap gap-3">
                {/* Primary action button */}
                <button className="bg-gradient-brand text-white px-6 py-2 rounded-lg hover:shadow-neon-cyan transition-all duration-300 font-medium">
                  Send Message
                </button>

                {/* Secondary button */}
                <button className="bg-light-bg-tertiary dark:bg-dark-bg-tertiary text-light-text-primary dark:text-dark-text-primary border border-light-border dark:border-dark-border px-4 py-2 rounded-lg hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary transition-colors">
                  Clear Chat
                </button>

                {/* Icon button with glow effect */}
                <button className="p-2 rounded-lg bg-dark-accent-primary text-white hover:animate-glow transition-all">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Status indicators */}
            <div className="mt-6 space-y-3">
              <h3 className="text-light-text-secondary dark:text-dark-text-secondary font-medium">Status Indicators</h3>
              
              {/* Online status */}
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-dark-accent-success rounded-full animate-pulse-soft"></div>
                <span className="text-xs text-light-text-tertiary dark:text-dark-text-tertiary">Connected</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BipedChatDemo;