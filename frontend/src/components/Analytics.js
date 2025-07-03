import React, { useState, useEffect } from 'react';

function Analytics() {
  const [analyticsData, setAnalyticsData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch analytics data
    fetch('/api/analytics/portfolio')
      .then(response => response.json())
      .then(data => {
        setAnalyticsData(data);
        setLoading(false);
      })
      .catch(error => {
        console.error('Error fetching analytics:', error);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="card">
        <h2>📈 Analytics</h2>
        <div className="loading-spinner"></div>
        <p>Loading analytics data...</p>
      </div>
    );
  }

  return (
    <div>
      <div className="card">
        <h2>📈 Advanced Analytics Dashboard</h2>
        <p>Real-time data processing and business intelligence</p>
        
        <div className="grid">
          <div className="metric-card">
            <div className="metric-value">9</div>
            <div className="metric-label">Analytics Endpoints</div>
          </div>
          
          <div className="metric-card">
            <div className="metric-value">Real-time</div>
            <div className="metric-label">Data Processing</div>
          </div>
          
          <div className="metric-card">
            <div className="metric-value">Chart.js</div>
            <div className="metric-label">Visualization</div>
          </div>
        </div>
      </div>

      <div className="card">
        <h3>📊 Available Analytics</h3>
        <div className="grid">
          <div className="metric-card">
            <h4>Project Analytics</h4>
            <p>Project performance tracking and completion rates</p>
            <button className="btn btn-success" onClick={() => window.open('/api/analytics/portfolio', '_blank')}>
              View API
            </button>
          </div>
          
          <div className="metric-card">
            <h4>Service Insights</h4>
            <p>Service demand analysis and pricing trends</p>
            <button className="btn btn-success" onClick={() => window.open('/api/analytics/market', '_blank')}>
              View API
            </button>
          </div>
          
          <div className="metric-card">
            <h4>Quality Management</h4>
            <p>Quality scoring and issue tracking</p>
            <button className="btn btn-success" onClick={() => window.open('/api/analytics/risk', '_blank')}>
              View API
            </button>
          </div>
        </div>
      </div>

      <div className="card">
        <h3>🎯 Enhanced Dashboard</h3>
        <p>For the full analytics experience with interactive charts and real-time data:</p>
        <button className="btn btn-primary" onClick={() => window.open('/analytics-dashboard.html', '_blank')}>
          Open Enhanced Analytics Dashboard
        </button>
      </div>
    </div>
  );
}

export default Analytics;

