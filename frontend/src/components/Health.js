import React, { useState, useEffect } from 'react';

function Health() {
  const [healthData, setHealthData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch comprehensive health data
    fetch('/health')
      .then(response => response.json())
      .then(data => {
        setHealthData(data);
        setLoading(false);
      })
      .catch(error => {
        console.error('Error fetching health data:', error);
        setLoading(false);
      });
  }, []);

  const refreshHealth = () => {
    setLoading(true);
    fetch('/health')
      .then(response => response.json())
      .then(data => {
        setHealthData(data);
        setLoading(false);
      })
      .catch(error => {
        console.error('Error fetching health data:', error);
        setLoading(false);
      });
  };

  if (loading) {
    return (
      <div className="card">
        <h2>🔧 System Health</h2>
        <div className="loading-spinner"></div>
        <p>Loading system health data...</p>
      </div>
    );
  }

  return (
    <div>
      <div className="card">
        <h2>🔧 System Health Monitor</h2>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <p>Comprehensive system monitoring and diagnostics</p>
          <button className="btn btn-primary" onClick={refreshHealth}>
            🔄 Refresh
          </button>
        </div>
        
        <div className="grid">
          <div className="metric-card">
            <div className="metric-value">
              {healthData?.status === 'healthy' ? '✅' : '⚠️'}
            </div>
            <div className="metric-label">Overall Status</div>
          </div>
          
          <div className="metric-card">
            <div className="metric-value">{healthData?.timestamp?.split('T')[1]?.split('.')[0] || 'N/A'}</div>
            <div className="metric-label">Last Check</div>
          </div>
          
          <div className="metric-card">
            <div className="metric-value">{healthData?.environment || 'Unknown'}</div>
            <div className="metric-label">Environment</div>
          </div>
        </div>
      </div>

      {healthData?.checks && (
        <div className="card">
          <h3>🔍 Component Health</h3>
          <div className="grid">
            <div className="metric-card">
              <h4>Database</h4>
              <div className="metric-value">
                {healthData.checks.database?.status === 'healthy' ? '✅' : '❌'}
              </div>
              <div className="metric-label">
                {healthData.checks.database?.message || 'Status unknown'}
              </div>
            </div>
            
            <div className="metric-card">
              <h4>Redis Cache</h4>
              <div className="metric-value">
                {healthData.checks.redis?.status === 'healthy' ? '✅' : '⚠️'}
              </div>
              <div className="metric-label">
                {healthData.checks.redis?.message || 'Status unknown'}
              </div>
            </div>
            
            <div className="metric-card">
              <h4>Computer Vision</h4>
              <div className="metric-value">
                {healthData.checks.computer_vision?.available ? '✅' : '⚠️'}
              </div>
              <div className="metric-label">
                {healthData.checks.computer_vision?.mode || 'Status unknown'}
              </div>
            </div>
          </div>
        </div>
      )}

      {healthData?.system && (
        <div className="card">
          <h3>💻 System Information</h3>
          <div className="grid">
            <div className="metric-card">
              <h4>Python Version</h4>
              <div className="metric-value">{healthData.system.python_version || 'Unknown'}</div>
            </div>
            
            <div className="metric-card">
              <h4>Platform</h4>
              <div className="metric-value">{healthData.system.platform || 'Unknown'}</div>
            </div>
            
            <div className="metric-card">
              <h4>Uptime</h4>
              <div className="metric-value">{healthData.system.uptime || 'Unknown'}</div>
            </div>
          </div>
        </div>
      )}

      <div className="card">
        <h3>🔗 Health Endpoints</h3>
        <div className="grid">
          <div className="metric-card">
            <h4>Simple Health</h4>
            <button className="btn btn-success" onClick={() => window.open('/health/simple', '_blank')}>
              /health/simple
            </button>
          </div>
          
          <div className="metric-card">
            <h4>Dependencies</h4>
            <button className="btn btn-primary" onClick={() => window.open('/health/dependencies', '_blank')}>
              /health/dependencies
            </button>
          </div>
          
          <div className="metric-card">
            <h4>Full Health</h4>
            <button className="btn btn-warning" onClick={() => window.open('/health', '_blank')}>
              /health
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Health;

