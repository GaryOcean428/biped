import React, { useState, useEffect } from 'react';

function Dashboard({ systemStatus }) {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch dashboard metrics
    Promise.all([
      fetch('/api/analytics/portfolio').catch(() => ({ json: () => ({ error: 'Service unavailable' }) })),
      fetch('/api/analytics/market').catch(() => ({ json: () => ({ error: 'Service unavailable' }) })),
      fetch('/api/vision/status').catch(() => ({ json: () => ({ error: 'Service unavailable' }) }))
    ]).then(async responses => {
      const [portfolio, market, vision] = await Promise.all(
        responses.map(r => r.json ? r.json() : r)
      );
      
      setMetrics({ portfolio, market, vision });
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div className="card">
        <h2>📊 Dashboard</h2>
        <div className="loading-spinner"></div>
        <p>Loading dashboard metrics...</p>
      </div>
    );
  }

  return (
    <div>
      <div className="card">
        <h2>📊 Biped Platform Dashboard</h2>
        <p>Welcome to your enterprise trading and business management platform.</p>
        
        <div className="grid">
          <div className="metric-card">
            <div className="metric-value">
              {systemStatus?.status === 'healthy' ? '✅' : '⚠️'}
            </div>
            <div className="metric-label">System Status</div>
          </div>
          
          <div className="metric-card">
            <div className="metric-value">
              {systemStatus?.checks?.database?.status === 'healthy' ? '✅' : '❌'}
            </div>
            <div className="metric-label">Database</div>
          </div>
          
          <div className="metric-card">
            <div className="metric-value">
              {systemStatus?.checks?.redis?.status === 'healthy' ? '✅' : '⚠️'}
            </div>
            <div className="metric-label">Redis Cache</div>
          </div>
          
          <div className="metric-card">
            <div className="metric-value">
              {systemStatus?.checks?.computer_vision?.available ? '✅' : '⚠️'}
            </div>
            <div className="metric-label">Computer Vision</div>
          </div>
        </div>
      </div>

      <div className="card">
        <h3>🚀 Platform Features</h3>
        <div className="grid">
          <div className="metric-card">
            <h4>📈 Analytics Engine</h4>
            <p>Real-time data processing, portfolio analytics, and market intelligence</p>
            <button className="btn btn-primary" onClick={() => window.location.href = '/analytics'}>
              View Analytics
            </button>
          </div>
          
          <div className="metric-card">
            <h4>👁️ Computer Vision</h4>
            <p>AI-powered image analysis and quality control</p>
            <button className="btn btn-primary" onClick={() => window.location.href = '/vision'}>
              Vision Tools
            </button>
          </div>
          
          <div className="metric-card">
            <h4>🔧 System Health</h4>
            <p>Comprehensive monitoring and diagnostics</p>
            <button className="btn btn-primary" onClick={() => window.location.href = '/health'}>
              Health Check
            </button>
          </div>
        </div>
      </div>

      <div className="card">
        <h3>📊 Quick Stats</h3>
        <div className="grid">
          <div className="metric-card">
            <div className="metric-value">v2.0</div>
            <div className="metric-label">Platform Version</div>
          </div>
          
          <div className="metric-card">
            <div className="metric-value">Railway</div>
            <div className="metric-label">Deployment</div>
          </div>
          
          <div className="metric-card">
            <div className="metric-value">Enterprise</div>
            <div className="metric-label">Edition</div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;

