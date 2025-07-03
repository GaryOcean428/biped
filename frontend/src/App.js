import React, { useState } from 'react';
import './App.css';
import TradesMarketplace from './components/TradesMarketplace';
import BipedChatDemo from './components/BipedChatDemo';

function App() {
  const [currentView, setCurrentView] = useState('marketplace');

  return (
    <div className="App">
      {/* Navigation */}
      <nav className="bg-light-bg-secondary dark:bg-dark-bg-secondary p-4 shadow-lg">
        <div className="container mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-display font-bold bg-gradient-brand bg-clip-text text-transparent">
            Biped Platform
          </h1>
          <div className="space-x-4">
            <button 
              onClick={() => setCurrentView('marketplace')}
              className={`px-4 py-2 rounded-lg transition-colors ${
                currentView === 'marketplace' 
                  ? 'bg-gradient-brand text-white' 
                  : 'text-light-text-primary dark:text-dark-text-primary hover:bg-light-bg-tertiary dark:hover:bg-dark-bg-tertiary'
              }`}
            >
              Marketplace
            </button>
            <button 
              onClick={() => setCurrentView('chat-demo')}
              className={`px-4 py-2 rounded-lg transition-colors ${
                currentView === 'chat-demo' 
                  ? 'bg-gradient-brand text-white' 
                  : 'text-light-text-primary dark:text-dark-text-primary hover:bg-light-bg-tertiary dark:hover:bg-dark-bg-tertiary'
              }`}
            >
              Tailwind Demo
            </button>
          </div>
        </div>
      </nav>

      {/* Content */}
      {currentView === 'marketplace' && <TradesMarketplace />}
      {currentView === 'chat-demo' && <BipedChatDemo />}
    </div>
  );
}

export default App;

