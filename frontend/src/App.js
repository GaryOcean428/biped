import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import './App.css';

// Components
import Dashboard from './components/Dashboard';
import Analytics from './components/Analytics';
import Vision from './components/Vision';
import Health from './components/Health';

function App() {
  const [systemStatus, setSystemStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check system health on app load
    fetch('/health')
      .then(response => response.json())
      .then(data => {
        setSystemStatus(data);
        setLoading(false);
      })
      .catch(error => {
        console.error('Error fetching system status:', error);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <h2>Loading Biped Platform...</h2>
      </div>
    );
  }

  return (
    <Router>
      <div className="App">
        <header className="App-header">
          <nav className="navbar">
            <div className="nav-brand">
              <h1>🚀 Biped Platform v2.0</h1>
              <span className={`status-indicator ${systemStatus?.status === 'healthy' ? 'healthy' : 'warning'}`}>
                {systemStatus?.status === 'healthy' ? '✅ Operational' : '⚠️ Degraded'}
              </span>
            </div>
            <div className="nav-links">
              <Link to="/" className="nav-link">Dashboard</Link>
              <Link to="/analytics" className="nav-link">Analytics</Link>
              <Link to="/vision" className="nav-link">Vision</Link>
              <Link to="/health" className="nav-link">Health</Link>
            </div>
          </nav>
        </header>

        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard systemStatus={systemStatus} />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/vision" element={<Vision />} />
            <Route path="/health" element={<Health />} />
          </Routes>
        </main>

        <footer className="App-footer">
          <p>&copy; 2025 Biped Platform - Enterprise Trading & Business Management</p>
        </footer>
      </div>
    </Router>
  );
}

export default App;

