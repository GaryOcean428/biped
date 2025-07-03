import React, { useState, useEffect } from 'react';

function Dashboard({ systemStatus }) {
  const [stats, setStats] = useState(null);
  const [recentActivity, setRecentActivity] = useState([]);
  const [serviceCategories, setServiceCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch dashboard stats
      const statsResponse = await fetch('/api/dashboard/stats');
      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        setStats(statsData);
      }

      // Fetch recent activity
      const activityResponse = await fetch('/api/dashboard/recent-activity?limit=5');
      if (activityResponse.ok) {
        const activityData = await activityResponse.json();
        setRecentActivity(activityData.activity || []);
      }

      // Fetch service categories
      const categoriesResponse = await fetch('/api/dashboard/service-categories');
      if (categoriesResponse.ok) {
        const categoriesData = await categoriesResponse.json();
        setServiceCategories(categoriesData.categories || []);
      }

    } catch (err) {
      setError('Failed to load dashboard data');
      console.error('Dashboard data fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-AU', {
      style: 'currency',
      currency: 'AUD'
    }).format(amount || 0);
  };

  if (loading) {
    return (
      <div className="card">
        <h2>📊 Loading Dashboard...</h2>
        <div className="loading-spinner"></div>
        <p>Fetching real-time trades marketplace data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <h2>📊 Dashboard Error</h2>
        <p>{error}</p>
        <button className="btn btn-primary" onClick={fetchDashboardData}>Retry</button>
      </div>
    );
  }

  return (
    <div>
      <div className="card">
        <h2>📊 Biped Trades Marketplace Dashboard</h2>
        <p>Welcome to your trades and services marketplace platform.</p>
        
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

      {stats && (
        <div className="card">
          <h3>📈 Platform Statistics</h3>
          <div className="grid">
            <div className="metric-card">
              <div className="metric-value">{stats.platform_stats?.active_jobs || 0}</div>
              <div className="metric-label">Active Projects</div>
            </div>
            <div className="metric-card">
              <div className="metric-value">{stats.platform_stats?.total_jobs || 0}</div>
              <div className="metric-label">Total Jobs Posted</div>
            </div>
            <div className="metric-card">
              <div className="metric-value">{stats.platform_stats?.completed_jobs || 0}</div>
              <div className="metric-label">Completed Projects</div>
            </div>
            <div className="metric-card">
              <div className="metric-value">{stats.platform_stats?.total_providers || 0}</div>
              <div className="metric-label">Service Providers</div>
            </div>
            <div className="metric-card">
              <div className="metric-value">{stats.platform_stats?.total_customers || 0}</div>
              <div className="metric-label">Customers</div>
            </div>
            <div className="metric-card">
              <div className="metric-value">{stats.platform_stats?.recent_jobs_30d || 0}</div>
              <div className="metric-label">New Jobs (30d)</div>
            </div>
          </div>
        </div>
      )}

      <div className="card">
        <h3>🔧 Service Categories</h3>
        <div className="grid">
          {serviceCategories.length > 0 ? (
            serviceCategories.map(category => (
              <div key={category.id} className="metric-card">
                <h4>{category.icon || '🔧'} {category.name}</h4>
                <p>{category.description}</p>
                <div className="service-stats">
                  <small>{category.total_jobs} jobs • {category.total_providers} providers</small>
                </div>
              </div>
            ))
          ) : (
            <div className="metric-card">
              <h4>🔧 Plumbing</h4>
              <p>Water, drainage, and pipe services</p>
              <small>Loading data...</small>
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <h3>📋 Recent Activity</h3>
        {recentActivity.length > 0 ? (
          <div className="activity-feed">
            {recentActivity.map((activity, index) => (
              <div key={`${activity.type}-${activity.id}-${index}`} className="activity-item">
                <div className="activity-type">
                  {activity.type === 'job' ? '💼' : '⭐'}
                </div>
                <div className="activity-content">
                  <h4>{activity.title}</h4>
                  <p>{activity.description}</p>
                  {activity.service && <span className="activity-service">{activity.service}</span>}
                  {activity.rating && <span className="activity-rating">Rating: {activity.rating}/5</span>}
                  <small className="activity-date">{formatDate(activity.timestamp)}</small>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p>No recent activity to display. Start by posting jobs or onboarding providers!</p>
        )}
      </div>

      {stats?.top_providers && stats.top_providers.length > 0 && (
        <div className="card">
          <h3>⭐ Top Rated Providers</h3>
          <div className="grid">
            {stats.top_providers.map((provider, index) => (
              <div key={index} className="metric-card">
                <h4>{provider.business_name || provider.name}</h4>
                <p>Rating: {provider.rating.toFixed(1)}/5.0</p>
                <small>Jobs Completed: {provider.jobs_completed}</small>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="card">
        <h3>🚀 Platform Features</h3>
        <div className="grid">
          <div className="metric-card">
            <h4>📊 Project Analytics</h4>
            <p>Real-time project tracking, service insights, and business analytics</p>
            <button className="btn btn-primary" onClick={() => window.location.href = '/analytics'}>
              View Analytics
            </button>
          </div>
          
          <div className="metric-card">
            <h4>👁️ Quality Control</h4>
            <p>AI-powered image analysis and work quality assessment</p>
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
        <h3>📊 Platform Info</h3>
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
            <div className="metric-value">Marketplace</div>
            <div className="metric-label">Edition</div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;

